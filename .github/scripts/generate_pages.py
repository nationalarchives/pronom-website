import json
import os
import re
import sys
from datetime import datetime
from urllib import request

from jinja2 import (
    ChoiceLoader,
    Environment,
    FileSystemLoader,
    PackageLoader,
    select_autoescape,
)

env = Environment(
    loader=ChoiceLoader(
        [
            FileSystemLoader("./lambdas/templates"),
            PackageLoader("tna_frontend_jinja"),
        ]
    ),
    autoescape=select_autoescape(),
)

bucket_name = "tna-pronom-signatures-spike"


def get_summary(data):
    identifiers = ", ".join(
        [
            f"{identifier['identifierType']}: {identifier['identifierText']}"
            for identifier in data["identifiers"]
        ]
    )

    def str_for_attr(attr):
        if attr in data:
            if data[attr] == "":
                return None
            else:
                return data[attr]

    return {
        "Name": str_for_attr("formatName"),
        "Version": str_for_attr("version"),
        "Identifiers": identifiers,
        "Format Type": str_for_attr("formatTypes"),
        "Family": str_for_attr("formatFamilies"),
        "Disclosure": str_for_attr("formatDisclosure"),
        "Description": str_for_attr("formatDescription"),
        "Note": str_for_attr("formatNote"),
    }


def create_detail(puid, json_data, all_actors):
    details_template = env.get_template("details.html")
    summary = get_summary(json_data)
    summary_args = {
        "results": [summary],
        "developedBy": (
            all_actors[json_data["developedBy"]] if "developedBy" in json_data else None
        ),
        "supportedBy": (
            all_actors[json_data["supportedBy"]] if "supportedBy" in json_data else None
        ),
        "source": all_actors[json_data["source"]] if "source" in json_data else None,
    }
    signatures = json_data["internalSignatures"]
    return details_template.render(
        name=summary["Name"],
        summary=summary_args,
        signatures=signatures,
        containers=json_data.get("containerSignatures", []),
    )


def create_actor(data):
    def format_date():
        return datetime.strptime(data["sourceDate"], "%Y-%m-%d").strftime("%d %b %Y")

    return {
        "Address": data["address"] if "address" in data else "",
        "Country": data["addressCountry"] if "addressCountry" in data else "",
        "Support Website": data["supportWebsite"] if "supportWebsite" in data else "",
        "Company Website": data["companyWebsite"] if "companyWebsite" in data else "",
        "Contact": data["contact"] if "contact" in data else "",
        "Source": data["source"] if "source" in data else "",
        "Source Date": format_date() if "sourceDate" in data else "",
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
    return env.get_template("home.html").render()


def create_search():
    return env.get_template("search.html").render()


path = sys.argv[1]


def create_file_list():
    with request.urlopen(
        "https://d21gi86t6uhf68.cloudfront.net/signatures.json"
    ) as url:
        all_signatures = json.load(url)

    signatures = sorted(
        all_signatures["signatures"],
        key=lambda k: int(re.search(r"(\d+)", k["location"]).group(1)),
    )
    container_signatures = all_signatures["container_signatures"]

    return env.get_template("signature_list.html").render(
        signature_data=signatures, container_signature_data=container_signatures
    )


def run():
    with open("site/error", "w") as error_page:
        error_page.write(env.get_template("error.html").render())
    with open("site/signature-list", "w") as signature_list:
        signature_list.write(create_file_list())

    with open("site/home", "w") as home:
        home.write(create_home())

    with open("site/search", "w") as search:
        search.write(create_search())

    with open("site/submission-received", "w") as search:
        search.write(create_search())

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
                puid = f'{sub_dir}/{file.split(".")[0]}'
                loaded_json = json.load(sig_json)
                all_json_files[puid] = loaded_json
                json_by_id[loaded_json["fileFormatID"]] = puid

    actor_select = [{"text": "", "value": 0}]
    for actor_json in all_actors.values():
        actor_select.append(
            {"text": actor_json["name"], "value": actor_json["actorId"]}
        )

    actor_select = sorted(actor_select, key=lambda x: x["text"])

    for puid, json_data in all_json_files.items():
        with open(f"site/{puid}", "w") as output:
            output.write(create_detail(puid, json_data, all_actors))

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
