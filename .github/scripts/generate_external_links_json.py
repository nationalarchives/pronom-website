"""
This script reads the s3://<bucket>/loc-fdd/fdd_puid_mapping.csv file and converts the data into a JSON file
that contains the necessary information for each puid to generate external links. This JSON is then fed to the
template engine to generate the external links section on the details page. It expects the bucket name to be
passed as the first argument to the script.

It does it in following steps:
1. It reads the CSV file from s3://<bucket>/loc-fdd/fdd_puid_mapping.csv
2. Parse the CSV and extract the necessary information for each puid and generate a dictionary with entries like
    {
        "fmt/6": [{"Location": "https://www.loc.gov/preservation/digital/formats/fdd/fdd000001", "Name": "WAVE Audio File Format"}],
    }
3. Write the JSON file into the folder locally for consumption by the template engine.

If there is an error anywhere in the process, that error is logged but the script does not fail.
"""

import csv
import io
import json
import re
import sys
from dataclasses import asdict, dataclass

import boto3
import requests

REQUEST_TIMEOUT = 60
FDD_MAPPING_SOURCE_FILE_KEY = "loc-fdd/fdd_puid_mapping.csv"
FDD_URL_PREFIX = "https://www.loc.gov/preservation/digital/formats/fdd/"


@dataclass(frozen=True, order=True)
class FddMapping:
    Location: str
    Name: str


def generate_fdd_mappings_dict(
    bucket: str, session: requests.Session, s3_client
) -> dict[str, set[FddMapping]]:
    mappings: dict[str, set[FddMapping]] = {}
    puid_pattern = re.compile(
        r"https://www\.nationalarchives\.gov\.uk/PRONOM/\}?((?:x-)?fmt/\d+)\b"
    )
    response = s3_client.get_object(Bucket=bucket, Key=FDD_MAPPING_SOURCE_FILE_KEY)
    with io.TextIOWrapper(
        response["Body"], encoding="utf-8-sig", newline=""
    ) as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            for puid in puid_pattern.findall(row["PRONOM_Note"]):
                mappings.setdefault(puid, set()).add(
                    FddMapping(
                        Location=f"{FDD_URL_PREFIX}{row['LC_Unique_ID']}",
                        Name=row["LC_Long_Name"],
                    )
                )
    return mappings


def main():
    persistent_data_bucket = sys.argv[1]
    print(
        f"Generating external links JSON from s3://{persistent_data_bucket}/{FDD_MAPPING_SOURCE_FILE_KEY}"
    )
    s3_client = boto3.client("s3")
    with requests.Session() as session:
        puid_fdd_mappings = generate_fdd_mappings_dict(
            persistent_data_bucket, session, s3_client
        )

    with open("fdd_puid_mapping.json", "w", encoding="utf-8") as output_file:
        json.dump(
            {
                key: [asdict(fdd) for fdd in sorted(value)]
                for key, value in puid_fdd_mappings.items()
            },
            output_file,
            indent=2,
        )


if __name__ == "__main__":
    main()
