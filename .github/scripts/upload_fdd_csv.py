"""
This script reads the FDD->PUID mapping CSV from the Library of Congress website and uploads it to the persistent
data S3 bucket. It expects the bucket name to be passed as the first argument to the script.
It does it in following steps:
1. It reads the HTML page at https://www.loc.gov/preservation/digital/formats/fdd/fdd_puid_qid.shtml
2. Parse the HTML and find all links for the CSV files
3. Find the latest CSV file based on the date in the filename
4. Read the latest CSV file and stream it to s3://<bucket>/loc-fdd/fdd_puid_mapping.csv, thus, there will ever be
    only one such file in the bucket. It tags the object with the source URL of the CSV file so that it can be
    identified if needed.

If there is an error anywhere in the process, that error is logged but the script does not fail.
"""

import re
import shutil
import sys
import tempfile
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit

import boto3
import requests
from boto3.exceptions import S3UploadFailedError
from botocore.exceptions import BotoCoreError, ClientError

FDD_PUID_MAPPING_PAGE_URL = (
    "https://www.loc.gov/preservation/digital/formats/fdd/fdd_puid_qid.shtml"
)
REQUEST_TIMEOUT = 60
FDD_MAPPING_SOURCE_FILE_KEY = "loc-fdd/fdd_puid_mapping.csv"


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


def latest_mapping_url(html_page_as_string: str) -> str:
    parser = FddPuidMappingPageParser()
    parser.feed(html_page_as_string)
    if not parser.links:
        raise ValueError(
            f"No dated mapping CSV links found on {FDD_PUID_MAPPING_PAGE_URL}"
        )
    latest = max(parser.links)[1]
    print(
        f"Found {len(parser.links)} mapping CSV links on {FDD_PUID_MAPPING_PAGE_URL}, using the latest one: {latest}"
    )
    return latest


def update_latest_mappings_from_loc_to_s3(
    bucket: str, session: requests.Session, s3_client
):
    try:
        print(f"Browsing the page: {FDD_PUID_MAPPING_PAGE_URL}")
        with session.get(
            FDD_PUID_MAPPING_PAGE_URL, timeout=REQUEST_TIMEOUT
        ) as response:
            response.raise_for_status()
            csv_url = latest_mapping_url(response.text)

        print(f"Using latest CSV: {csv_url} to upload to PRONOM persistent bucket")

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
                csv_file,
                bucket,
                FDD_MAPPING_SOURCE_FILE_KEY,
                ExtraArgs={"ContentType": "text/csv", "Tagging": f"source={csv_url}"},
            )
        print(f"Uploaded s3://{bucket}/{FDD_MAPPING_SOURCE_FILE_KEY}")
    except (
        requests.RequestException,
        S3UploadFailedError,
        BotoCoreError,
        ClientError,
    ) as error:
        print(
            f"Warning: Could not refresh the LOC mapping: {error}. ",
            file=sys.stderr,
        )


def main():
    print("Starting the LOC FDD->PUID mapping refresh script")
    persistent_data_bucket = sys.argv[1]
    s3_client = boto3.client("s3")
    with requests.Session() as session:
        print(
            f"Refreshing the LOC FDD->PUID mapping in s3://{persistent_data_bucket}/{FDD_MAPPING_SOURCE_FILE_KEY}"
        )
        update_latest_mappings_from_loc_to_s3(
            persistent_data_bucket, session, s3_client
        )


if __name__ == "__main__":
    main()
