"""
This script reads the FDD->PUID mapping CSV from the Library of Congress website and uploads it to an S3 bucket.
It then reads the uploaded file and generates a JSON file containing the mapping of PUIDs to FDDs. The JSON
file is then used to create hyperlinks in the PRONOM website.

It does it in following steps:
1. It reads the HTML page at https://www.loc.gov/preservation/digital/formats/fdd/fdd_puid_qid.shtml 
2. Parse the HTML and find all links for the CSV files 
3. Find the latest CSV file based on the date in the filename
4. Read the latest CSV file and stream it to s3://<bucket>/loc-fdd/fdd_puid_mapping.csv,
   overwriting the existing object only after the CSV has downloaded successfully. Tag the
   object with the source URL of the CSV file.
5. Generate a dictionary of PUIDs to FDDs from the uploaded mapping CSV and return it
    {
        "fmt/6": [{"Location": "https://www.loc.gov/preservation/digital/formats/fdd/fdd000001", "Name": "WAVE Audio File Format"}],
    }
6. The dictionary is serialized to JSON and uploaded to loc/fdd_puid_mapping.json in S3
   so that it can be used by the PRONOM website to create hyperlinks to the FDDs.
"""

import csv
import io
import json
import re
import shutil
import sys
import tempfile
from dataclasses import asdict, dataclass
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit

import boto3
from boto3.exceptions import S3UploadFailedError
from botocore.exceptions import BotoCoreError, ClientError
import requests

FDD_PUID_MAPPING_PAGE_URL = "https://www.loc.gov/preservation/digital/formats/fdd/fdd_puid_qid.shtml"
FDD_URL_PREFIX = "https://www.loc.gov/preservation/digital/formats/fdd/"
REQUEST_TIMEOUT = 60
FDD_MAPPING_SOURCE_FILE_KEY = "loc-fdd/fdd_puid_mapping.csv"
FDD_PUID_MAPPING_JSON_KEY = "loc/fdd_puid_mapping.json"


@dataclass(frozen=True, order=True)
class FddMapping:
    Location: str
    Name: str


class FddPuidMappingPageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links: list[tuple[str, str]] = []

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return

        for name, value in attrs:
            if name != "href" or not value:
                continue
            url = urljoin(FDD_PUID_MAPPING_PAGE_URL, value)
            filename = urlsplit(url).path.rsplit("/", 1)[-1]
            match = re.fullmatch(r"fdd-puid-qid-(\d{8})\.csv", filename)
            if match:
                self.links.append((match.group(1), url))

def generate_fdd_mappings_dict(response) -> dict[str, set[FddMapping]]:
    mappings: dict[str, set[FddMapping]] = {}
    puid_pattern = re.compile(
        r"https://www\.nationalarchives\.gov\.uk/PRONOM/\}?((?:x-)?fmt/\d+)\b"
    )
    with io.TextIOWrapper(response["Body"], encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            for puid in puid_pattern.findall(row["PRONOM_Note"]):
                mappings.setdefault(puid, set()).add(
                    FddMapping(Location=f"{FDD_URL_PREFIX}{row['LC_Unique_ID']}", Name=row["LC_Long_Name"])
                )
    return mappings

def latest_mapping_url(html_page_as_string: str) -> str:
    parser = FddPuidMappingPageParser()
    parser.feed(html_page_as_string)
    if not parser.links:
        raise ValueError(f"No dated mapping CSV links found on {FDD_PUID_MAPPING_PAGE_URL}")
    latest = max(parser.links)[1]
    print(f"Found {len(parser.links)} mapping CSV links on {FDD_PUID_MAPPING_PAGE_URL}, using the latest one: {latest}")
    return latest

def update_latest_mappings_from_loc_to_s3(
    bucket: str, session: requests.Session, s3_client
):
    try:
        print(f"Browsing the page: {FDD_PUID_MAPPING_PAGE_URL}")
        with session.get(FDD_PUID_MAPPING_PAGE_URL, timeout=REQUEST_TIMEOUT) as response:
            response.raise_for_status()
            csv_url = latest_mapping_url(response.text)

        print(f"Using latest CSV: {csv_url} to generate the FDD->PUID mapping")

        with tempfile.SpooledTemporaryFile(max_size=8 * 1024 * 1024) as csv_file:
            print(f"Downloading {csv_url}")
            with session.get(csv_url, stream=True, timeout=REQUEST_TIMEOUT) as response:
                response.raise_for_status()
                response.raw.decode_content = True
                shutil.copyfileobj(response.raw, csv_file)
            print(f"Downloaded {csv_url} ({csv_file.tell()} bytes)")
            csv_file.seek(0)
            print(f"Uploading {csv_url} -> s3://{bucket}/{FDD_MAPPING_SOURCE_FILE_KEY}")
            s3_client.upload_fileobj(
                csv_file, bucket, FDD_MAPPING_SOURCE_FILE_KEY, ExtraArgs={"ContentType": "text/csv", "Tagging": f"source={csv_url}"}
            )
    except Exception as error:
        print(
            f"Warning: Could not refresh the LOC mapping: {error}. "
            f"Continuing with existing s3://{bucket}/{FDD_MAPPING_SOURCE_FILE_KEY}.",
            file=sys.stderr,
        )

    print(f"Uploaded s3://{bucket}/{FDD_MAPPING_SOURCE_FILE_KEY}")

def generate_fdd_links_json(
        bucket: str, session: requests.Session, s3_client
) -> dict[str, set[FddMapping]]:
    update_latest_mappings_from_loc_to_s3(bucket, session, s3_client)
    response = s3_client.get_object(Bucket=bucket, Key=FDD_MAPPING_SOURCE_FILE_KEY)
    return generate_fdd_mappings_dict(response)

def main():
    bucket = sys.argv[1]
    s3_client = boto3.client("s3")
    with requests.Session() as session:
        puid_fdd_mappings = generate_fdd_links_json(
            bucket, session, s3_client
        )
    s3_client.put_object(
        Bucket=bucket,
        Key=FDD_PUID_MAPPING_JSON_KEY,
        Body=json.dumps(
            {
                key: [asdict(fdd) for fdd in sorted(value)]
                for key, value in puid_fdd_mappings.items()
            },
            indent=2
        ).encode("utf-8"),
        ContentType="application/json",
    )
if __name__ == "__main__":
    main()
