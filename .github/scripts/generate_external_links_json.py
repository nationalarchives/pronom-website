"""
This script reads the s3://<bucket>/loc-fdd/fdd_puid_mapping.csv file or a local CSV and converts the data into a JSON file
that contains the necessary information for each puid to generate external links. This JSON is then fed to the
template engine to generate the external links section on the details page. It expects the bucket name to be
passed as the first argument to the script, or a local CSV path passed with --local-csv.

It does it in following steps:
1. It reads the CSV file from s3://<bucket>/loc-fdd/fdd_puid_mapping.csv or a local path.
2. Parse the CSV and extract the necessary information for each puid and generate a dictionary with entries like
    {
        "fmt/6": [{"Location": "https://www.loc.gov/preservation/digital/formats/fdd/fdd000001", "Name": "WAVE Audio File Format"}],
    }
3. Write the JSON file into the current directory for consumption by the template engine.
"""

import argparse
import csv
import io
import json
import re
from dataclasses import asdict, dataclass
from typing import TextIO

import boto3

FDD_MAPPING_SOURCE_FILE_KEY = "loc-fdd/fdd_puid_mapping.csv"
FDD_URL_PREFIX = "https://www.loc.gov/preservation/digital/formats/fdd/"


@dataclass(frozen=True, order=True)
class FddMapping:
    Location: str
    Name: str


def generate_fdd_mappings_from_csv(csv_file: TextIO) -> dict[str, set[FddMapping]]:
    mappings: dict[str, set[FddMapping]] = {}
    puid_pattern = re.compile(
        r"https://www\.nationalarchives\.gov\.uk/PRONOM/\}?((?:x-)?fmt/\d+)\b"
    )
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


def generate_fdd_mappings_dict(bucket: str, s3_client) -> dict[str, set[FddMapping]]:
    response = s3_client.get_object(Bucket=bucket, Key=FDD_MAPPING_SOURCE_FILE_KEY)
    with io.TextIOWrapper(
        response["Body"], encoding="utf-8-sig", newline=""
    ) as csv_file:
        return generate_fdd_mappings_from_csv(csv_file)


def main():
    parser = argparse.ArgumentParser(description="Generate external links JSON")
    parser.add_argument("bucket", nargs="?", help="persistent data S3 bucket")
    parser.add_argument(
        "--local-csv", help="read mappings from a local CSV instead of S3"
    )
    args = parser.parse_args()
    if bool(args.bucket) == bool(args.local_csv):
        parser.error("provide either a bucket or --local-csv")

    if args.local_csv:
        print(f"Generating external links JSON from {args.local_csv}")
        with open(args.local_csv, encoding="utf-8-sig", newline="") as csv_file:
            puid_fdd_mappings = generate_fdd_mappings_from_csv(csv_file)
    else:
        print(
            f"Generating external links JSON from s3://{args.bucket}/{FDD_MAPPING_SOURCE_FILE_KEY}"
        )
        s3_client = boto3.client("s3")
        puid_fdd_mappings = generate_fdd_mappings_dict(args.bucket, s3_client)

    with open("fdd_puid_mapping.json", "w", encoding="utf-8") as output_file:
        json.dump(
            {
                key: [asdict(fdd) for fdd in sorted(value)]
                for key, value in puid_fdd_mappings.items()
            },
            output_file,
        )


if __name__ == "__main__":
    main()
