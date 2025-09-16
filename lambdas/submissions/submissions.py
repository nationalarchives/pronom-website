import base64
import io
import json
import zipfile
from datetime import datetime
from urllib.parse import parse_qs

import boto3
from fastcore.net import HTTPError
from ghapi.all import GhApi

tna_name = "The National Archives"
tna_email = "digitalpreservation@nationalarchives.gov.uk"
owner = "tna-pronom"
parent_owner = "nationalarchives"
repo = "pronom-signatures"


def get_token():
    client = boto3.client("ssm")
    return client.get_parameter(Name="/github/token", WithDecryption=True)["Parameter"][
        "Value"
    ]


def create_branch(token):
    api = GhApi(token=token)
    suffix = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    branch_name = f"refs/heads/pronom-submission-branch-{suffix}"
    api.repos.merge_upstream(owner, repo, "develop")
    sha = api.git.get_ref(owner, repo, "heads/develop")["object"]["sha"]
    api.git.create_ref(owner, repo, branch_name, sha)
    return branch_name


def get_json_files(token, branch_name):
    api = GhApi(token=token)
    repo_archive = api.repos.download_zipball_archive(owner, repo, branch_name)
    zip_stream = io.BytesIO(repo_archive)
    with zipfile.ZipFile(zip_stream) as zip_file:
        file_names = zip_file.namelist()
        signature_files = [
            name
            for name in file_names
            if "/signatures/" in name and name.endswith(".json")
        ]
        actor_files = [
            name for name in file_names if "/actors/" in name and name.endswith(".json")
        ]
        signature_json = {
            "/".join(name.split("/")[2:]): json.loads(zip_file.read(name))
            for name in signature_files
        }
        actor_json = {
            "/".join(name.split("/")[2:]): json.loads(zip_file.read(name))
            for name in actor_files
        }
    return signature_json, actor_json


def edit_format(puid, body_json, json_files):
    del body_json["puid"]
    format_json = json_files[f"{puid}.json"]
    changed = False

    if "identifierType" in body_json and "identifierText" in body_json.copy():
        identifiers = format_json["identifiers"] if "identifiers" in format_json else []
        new_identifier = {
            "identifierText": body_json["identifierText"],
            "identifierType": body_json["identifierType"],
        }
        identifiers.append(new_identifier)
        format_json["identifiers"] = identifiers
        del body_json["identifierType"]
        del body_json["identifierText"]
        changed = True

    if "relationshipType" in body_json and "relatedFormatName" in body_json:
        relationships = (
            format_json["relationships"] if "relationships" in format_json else []
        )
        if f"{body_json['relatedFormatName']}.json" not in json_files:
            raise ValueError(f"{body_json['relatedFormatName']} does not exist")
        new_relationship = {
            "relationshipType": body_json["relationshipType"],
            "relatedFormatID": json_files[f"{body_json['relatedFormatName']}.json"][
                "fileFormatID"
            ],
        }
        relationships.append(new_relationship)
        format_json["relationships"] = relationships
        del body_json["relationshipType"]
        del body_json["relatedFormatName"]
        changed = True

    def update_actor(field_name):
        existing_value = format_json.get(field_name)
        body_value = body_json.get(field_name)
        if body_value and body_value != "0":
            if existing_value is None or existing_value != int(body_value):
                format_json[field_name] = int(body_value) if body_value else None
                return True
        return False

    supported_by_updated = update_actor("supportedBy")
    developed_by_updated = update_actor("developedBy")
    del body_json["submissionType"]
    excluded_keys = [
        "supportedBy",
        "developedBy",
        "contributorName",
        "changeDescription",
    ]
    for key, value in body_json.items():
        if format_json.get(key) != body_json[key] and key not in excluded_keys:
            format_json[key] = body_json[key]
            changed = True
    return changed or supported_by_updated or developed_by_updated


def create_pull_request(
    token, message, path, content_bytes, branch_name, author_name, body_text
):
    api = GhApi(token=token)
    base64_content = base64.b64encode(content_bytes).decode()
    committer = {"name": tna_name, "email": tna_email}

    file_contents_args = {
        "owner": owner,
        "repo": repo,
        "message": message,
        "path": path,
        "committer": committer,
        "author": {"name": author_name, "email": tna_email},
        "content": base64_content,
        "branch": branch_name,
    }
    try:
        existing_sha = api.repos.get_content(owner, repo, path, branch_name)["sha"]
        file_contents_args["sha"] = existing_sha
    except HTTPError:
        pass

    api.repos.create_or_update_file_contents(**file_contents_args)
    head = f"{owner}:{branch_name}"
    base = "develop"
    res = api.pulls.create(
        parent_owner, repo, message, head=head, base=base, body=body_text
    )
    return res["number"]


def add_actor(body_json):
    actor = {}

    def add_if_not_empty(key):
        if key in body_json:
            actor[key] = body_json[key]

    add_if_not_empty("name")
    add_if_not_empty("address")
    add_if_not_empty("addressCountry")
    add_if_not_empty("companyWebsite")
    add_if_not_empty("supportWebsite")
    return actor


def error(e):
    return {
        "statusCode": 500,
        "body": f"An error occurred: {str(e)}",
        "headers": {"Content-Type": "text/html"},
    }


def lambda_handler(event, context):  # noqa: C901
    token = get_token()
    body_json = {k: v[0] for k, v in parse_qs(event["body"]).items()}
    branch_name = create_branch(token)
    json_files, actor_files = get_json_files(token, branch_name)

    submission_type = body_json["submissionType"]

    def get_body_text(pr_message):
        if "changeDescription" in body_json:
            body = body_json["changeDescription"]
            del body_json["changeDescription"]
        else:
            body = pr_message
        return body

    if body_json.get("contributorName") and body_json["contributorName"] != "":
        author_name = body_json["contributorName"]
        del body_json["contributorName"]
    else:
        author_name = "The National Archives"
    if submission_type == "edit-format":
        puid = body_json["puid"]
        message = f"Submission to change {puid}"
        body_text = get_body_text(message)
        format_json = json_files[f"{puid}.json"]
        changed = edit_format(puid, body_json, json_files)
        if changed:
            path = f"signatures/{puid}.json"
            content_bytes = json.dumps(format_json, indent=2).encode()
            create_pull_request(
                token, message, path, content_bytes, branch_name, author_name, body_text
            )
    elif submission_type == "add-actor":
        message = "Submission to add a new organisation"
        body_text = get_body_text(message)
        actor = add_actor(body_json)
        if len(actor) > 0:
            file_name = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
            path = f"submissions/actors/{file_name}.json"
            content_bytes = json.dumps(actor, indent=2).encode()

            create_pull_request(
                token, message, path, content_bytes, branch_name, author_name, body_text
            )
    elif submission_type == "edit-actor":
        actor_id = body_json["actorId"]
        actor = actor_files[f"{actor_id}.json"]
        message = f"Submission to change {actor['name']}"
        body_text = get_body_text(message)
        body_json["actorId"] = int(actor_id)
        del body_json["submissionType"]
        if not actor_files.get(f"{actor_id}.json"):
            raise ValueError(f"Actor {actor_id} does not exist")
        changed = False
        for key in body_json.keys():
            if key not in actor or actor[key] != body_json[key]:
                changed = True
        if changed:
            for key, value in body_json.items():
                actor[key] = value
            path = f"actors/{actor_id}.json"
            content_bytes = json.dumps(actor, indent=2).encode()

            create_pull_request(
                token, message, path, content_bytes, branch_name, author_name, body_text
            )
    elif submission_type == "add-format":
        message = "New submission"
        body_text = get_body_text(message)
        del body_json["submissionType"]

        signature_json = {}

        for key, value in body_json.copy().items():
            if key.startswith("signature-"):
                if value.isnumeric():
                    signature_json[key.replace("signature-", "")] = int(value)
                else:
                    signature_json[key.replace("signature-", "")] = value
                del body_json[key]

        if len(signature_json) > 0:
            body_json["internalSignatures"] = [signature_json]
        file_name = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        path = f"submissions/{file_name}.json"
        content_bytes = json.dumps(body_json, indent=2).encode()
        create_pull_request(
            token, message, path, content_bytes, branch_name, author_name, body_text
        )
    else:
        return error(Exception(f"submissionType {submission_type} not found"))

    return {
        "statusCode": 302,
        "headers": {"Content-Type": "text/html", "Location": "/submissions-received"},
    }
