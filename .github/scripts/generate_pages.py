import csv
import json
import os
import re
import sys
import urllib
from datetime import datetime
from pathlib import Path
from urllib.request import Request

from jinja2 import (
    ChoiceLoader,
    Environment,
    FileSystemLoader,
    PackageLoader,
    select_autoescape,
)
from tna_utilities.string import slugify

env = Environment(
    loader=ChoiceLoader(
        [
            FileSystemLoader("./lambdas/templates"),
            PackageLoader("tna_frontend_jinja"),
        ]
    ),
    autoescape=select_autoescape(),
)
env.add_extension("jinja2.ext.do")
env.filters["slugify"] = slugify

bucket_name = "tna-pronom-signatures-spike"


def get_summary(data):
    identifiers = (
        {
            identifier["identifierType"]: identifier["identifierText"]
            for identifier in data["identifiers"]
        }
        if "identifiers" in data
        else None
    )

    format_types = data.get("formatTypes", None)

    return {
        "Name": data.get("formatName", None),
        "Version": data.get("version", None),
        "Identifiers": identifiers,
        "Format Type": format_types.split(", ") if format_types else None,
        "Family": data.get("formatFamilies", None),
        "Disclosure": data.get("formatDisclosure", None),
        "Description": data.get("formatDescription", None),
        "Note": data.get("formatNote", None),
    }


def get_relationships(json_data, json_by_id):
    relationships = json_data["relationships"]
    relationship_summary = []
    for relationship in relationships:
        relationship_json = json_by_id[relationship["relatedFormatID"]]
        relationship_puid = [
            idf["identifierText"]
            for idf in relationship_json["identifiers"]
            if idf["identifierType"] == "PUID"
        ][0]
        relationship_version = (
            f" {relationship_json['version']}"
            if relationship_json.get("version")
            else ""
        )
        summary = {
            "type": relationship["relationshipType"],
            "puid": relationship_puid,
            "name": relationship["relatedFormatName"] + relationship_version,
        }
        relationship_summary.append(summary)
    return relationship_summary


def get_file_extensions(json_data):
    external_signatures = (
        json_data["externalSignatures"] if "externalSignatures" in json_data else []
    )
    file_extension_list = [
        x for x in external_signatures if x["signatureType"] == "File extension"
    ]
    extension_names = [fe["externalSignature"] for fe in file_extension_list]
    return [extension for extension in extension_names if extension]


def create_detail(puid, json_data, all_actors, json_by_id, releases):
    details_template = env.get_template("details.html")
    summary = get_summary(json_data)
    summary_args = {
        "results": [summary],
        "relationships": get_relationships(json_data, json_by_id),
        "extensions": get_file_extensions(json_data),
        "developedBy": (
            all_actors[json_data["developedBy"]] if "developedBy" in json_data else None
        ),
        "supportedBy": (
            all_actors[json_data["supportedBy"]] if "supportedBy" in json_data else None
        ),
        "source": all_actors[json_data["source"]] if "source" in json_data else None,
    }
    signatures = json_data["internalSignatures"]
    changed_in_releases = [
        release
        + (
            "Added"
            if puid in [sig["puid"] for sig in details["New Records"]]
            or puid in [sig["puid"] for sig in details["New Signatures"]]
            else "Updated",
        )
        for release, details in releases.items()
        if any(
            sig["puid"] == puid
            for sig in (
                details["Updated Records"]
                + details["New Signatures"]
                + details["New Records"]
            )
        )
    ]
    return details_template.render(
        id=json_data.get("fileFormatID"),
        puid=puid,
        name=summary["Name"],
        summary=summary_args,
        signatures=signatures,
        containers=json_data.get("containerSignatures", []),
        releases=releases,
        changed_in_releases=changed_in_releases,
    )


def create_actor(data):
    def format_date():
        return datetime.strptime(data["sourceDate"], "%Y-%m-%d").strftime("%d %b %Y")

    return {
        "Address": data.get("address"),
        "Country": data.get("addressCountry"),
        "Support Website": data.get("supportWebsite"),
        "Company Website": data.get("companyWebsite"),
        "Contact": data.get("contact"),
        "Source": data.get("source"),
        "Source Date": format_date() if "sourceDate" in data else None,
    }


def create_signature_section():
    position_type_names = [
        "Absolute from BOF",
        "Absolute from EOF",
        "Variable",
        "Indirect From BOF",
        "Indirect From EOF",
    ]
    position_type_select = [{"value": x, "text": x} for x in position_type_names]
    position_type_select.insert(0, {"value": "", "text": ""})
    signature_template = env.get_template("signature.html")
    return signature_template.render(position_types=position_type_select)


def create_home():
    return env.get_template("index.html").render()


def create_search():
    return env.get_template("search.html").render()


def create_accessibility():
    return env.get_template("accessibility-statement.html").render()


path = sys.argv[1]


def create_file_list():
    with open("site/signatures.json") as sig_json_file:
        all_signatures = json.load(sig_json_file)

    signatures = sorted(
        all_signatures["signatures"],
        key=lambda k: int(re.search(r"(\d+)", k["location"]).group(1)),
    )
    signatures.reverse()
    container_signatures = all_signatures["container_signatures"]
    container_signatures.reverse()

    return env.get_template("signature_list.html").render(
        signature_data=signatures, container_signature_data=container_signatures
    )


def get_latest_release():
    req = Request(
        "https://api.github.com/repos/nationalarchives/pronom/releases/latest"
    )
    if github_token := os.environ.get("GITHUB_TOKEN", None):
        req.add_header("Authorization", f"Bearer {github_token}")
    req.add_header("Accept", "application/vnd.github+json")
    with urllib.request.urlopen(req) as response:
        return json.load(response)["name"]


def ordinal(n: int) -> str:
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def format_date(date_str: str) -> str:
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return f"{ordinal(dt.day)} {dt.strftime('%B %Y')}"


def get_releases():
    base_path = Path(path) / Path("changelogs")
    releases = {}
    latest_release = get_latest_release().upper()
    for file in os.listdir(Path(path) / Path("changelogs")):
        version = re.search(r"(v\d{2,4})", file).group().upper()
        date_match = re.search(r"(\d{4}-\d{2}-\d{2})", file)
        if int(version.lstrip("V")) <= int(latest_release.lstrip("V")) and date_match:
            date = format_date(date_match.group())
            releases[
                (
                    version,
                    date,
                )
            ] = {
                "New Records": [],
                "New Signatures": [],
                "Updated Records": [],
            }
            with open(base_path / Path(file)) as change_file:
                reader = csv.reader(change_file)
                for row in reader:
                    type_key = "New Signatures" if row[0] == "Signatures" else row[0]
                    releases[
                        (
                            version,
                            date,
                        )
                    ][type_key].append({"puid": row[1], "description": row[2]})

    sorted_releases = dict(
        sorted(
            releases.items(),
            key=lambda item: int(item[0][0].lstrip("V")),
            reverse=True,
        )
    )
    return sorted_releases, latest_release


def create_releases_page(releases, latest_release):
    items = [
        {"text": release[0], "href": f"#{release[0]}"} for release in releases.keys()
    ]
    return env.get_template("releases.html").render(
        releases=releases, items=items, latest_release=latest_release
    )


def create_release_page(release, details):
    return env.get_template("release.html").render(release=release, details=details)


def run():
    releases, latest_release = get_releases()

    with open("site/about", "w") as about_page:
        about_page.write(env.get_template("about.html").render())

    os.makedirs("site/releases", exist_ok=True)
    with open("site/releases.html", "w") as release_notes:
        release_notes.write(create_releases_page(releases, latest_release))
    for release, details in releases.items():
        release_version = release[0].lower()
        with open(f"site/releases/{release_version}", "w") as release_page:
            release_page.write(create_release_page(release, details))

    with open("site/error", "w") as error_page:
        error_page.write(env.get_template("error.html").render())

    with open("site/signature-list", "w") as signature_list:
        signature_list.write(create_file_list())

    with open("site/home", "w") as home:
        home.write(create_home())

    with open("site/accessibility-statement", "w") as accessibility:
        accessibility.write(create_accessibility())

    all_json_files = {}
    all_actors = {}
    json_by_id = {}

    for file in os.listdir(f"{path}/actors"):
        with open(f"{path}/actors/{file}") as actor_file:
            actor_json = json.load(actor_file)
            actor_id = actor_json["actorId"]
            all_actors[actor_id] = actor_json

    for sub_dir in ["fmt", "x-fmt"]:
        sig_files = os.listdir(f"{path}/signatures/{sub_dir}")
        for file in sig_files:
            json_path = f"{path}/signatures/{sub_dir}/{file}"
            with open(json_path, "r") as sig_json:
                puid = f"{sub_dir}/{file.split('.')[0]}"
                loaded_json = json.load(sig_json)
                all_json_files[puid] = loaded_json
                json_by_id[loaded_json["fileFormatID"]] = loaded_json

    for puid, json_data in all_json_files.items():
        with open(f"site/{puid}", "w") as output:
            output.write(
                create_detail(puid, json_data, all_actors, json_by_id, releases)
            )

    for actor_json in all_actors.values():
        actor_id = actor_json["actorId"]
        view_path = f"site/actor/{actor_id}"
        with open(view_path, "w") as actor_page:
            actor_details_template = env.get_template("actor_details.html")
            actor = create_actor(actor_json)
            name = actor_json["name"]
            actor_details = actor_details_template.render(
                results=actor, name=name, actorId=actor_id
            )
            actor_page.write(actor_details)


run()
