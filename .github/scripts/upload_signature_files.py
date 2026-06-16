import sys
from typing import Optional

import boto3
import requests


API_BASE = "https://api.github.com"


def github_headers() -> dict:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    return headers


def parse_next_link(link_header: Optional[str]) -> Optional[str]:
    if not link_header:
        return None

    parts = [part.strip() for part in link_header.split(",")]
    for part in parts:
        sections = [s.strip() for s in part.split(";")]
        if len(sections) < 2:
            continue

        url_part = sections[0]
        rel_part = sections[1]

        if rel_part == 'rel="next"' and url_part.startswith("<") and url_part.endswith(">"):
            return url_part[1:-1]

    return None


def iter_releases(owner: str, repo: str):
    url = f"{API_BASE}/repos/{owner}/{repo}/releases?per_page=100"

    session = requests.Session()
    session.headers.update(github_headers())

    while url:
        print(f"Fetching: {url}")
        response = session.get(url)
        response.raise_for_status()

        for release in response.json():
            yield release

        url = parse_next_link(response.headers.get("Link"))


def build_s3_key(prefix: str, asset_name: str) -> str:
    if not prefix:
        return asset_name
    return f"{prefix.rstrip('/')}/{asset_name}"


def stream_to_s3(
        asset_url: str,
        bucket: str,
        key: str,
        session: requests.Session,
        s3_client,
        content_type: Optional[str] = None,
) -> None:
    with session.get(asset_url, stream=True) as response:
        response.raise_for_status()

        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type

        s3_client.upload_fileobj(
            response.raw,
            bucket,
            key,
            ExtraArgs=extra_args if extra_args else None,
        )


def main():
    if len(sys.argv) != 2:
        print(
            f"Usage: python {sys.argv[0]} S3_BUCKET",
            file=sys.stderr,
        )
        sys.exit(1)

    owner = "nationalarchives"
    repo = "pronom"
    bucket = sys.argv[1]


    s3_client = boto3.client("s3")

    session = requests.Session()
    session.headers.update(github_headers())

    count = 0

    for release in iter_releases(owner, repo):
        assets = release.get("assets", [])
        if not assets:
            print(f"Skipping release {release.get('tag_name', '<unknown>')} (no assets)")
            continue

        for asset in assets:
            asset_name = asset["name"]
            asset_url = asset["browser_download_url"]
            content_type = asset.get("content_type") or "application/octet-stream"
            if asset_name.startswith("container-signature"):
                prefix = "container-signatures"
            else:
                prefix = "signatures"

            s3_key = build_s3_key(prefix, asset_name)

            print(f"Streaming {release.get('tag_name')} -> s3://{bucket}/{s3_key}")
            stream_to_s3(
                asset_url=asset_url,
                bucket=bucket,
                key=s3_key,
                session=session,
                s3_client=s3_client,
                content_type=content_type,
            )
            count += 1


    print(f"Uploaded {count} asset(s) to s3://{bucket}/{prefix}")


if __name__ == "__main__":
    main()