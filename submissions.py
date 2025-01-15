import json
from urllib.parse import parse_qs
from ghapi.all import GhApi
import io
import zipfile
from datetime import datetime
import base64
import boto3

client = boto3.client('ssm')
token = client.get_parameter(
    Name='/github/token',
    WithDecryption=True
)['Parameter']['Value']
api = GhApi(token=token)
tna_name = 'The National Archives'
tna_email = 'digitalpreservation@nationalarchives.gov.uk'
owner = 'mancuniansam'
parent_owner = 'nationalarchives'
repo = 'pronom-signatures'


def create_branch():
    suffix = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    branch_name = f'refs/heads/pronom-submission-branch-{suffix}'
    api.repos.merge_upstream(owner, repo, 'develop')
    sha = api.git.get_ref(owner, repo, 'heads/develop')['object']['sha']
    api.git.create_ref(owner, repo, branch_name, sha)
    return branch_name


def get_json_files(branch_name):
    repo_archive = api.repos.download_zipball_archive(owner, repo, branch_name)
    zip_stream = io.BytesIO(repo_archive)
    with zipfile.ZipFile(zip_stream) as zip_file:
        file_names = zip_file.namelist()
        signature_files = [name for name in file_names if '/signatures/' in name and name.endswith('.json')]
        return {'/'.join(name.split('/')[2:]): json.loads(zip_file.read(name)) for name in signature_files}


def lambda_handler(event, context):
    for record in event['Records']:
        body_json = {k: v[0] for k, v in parse_qs(record['body']).items()}
        branch_name = create_branch()
        json_files = get_json_files(branch_name)

        actors = {}
        for json_data in json_files.values():
            if 'developedBy' in json_data:
                actors[json_data['developedBy']['actorId']] = json_data['developedBy']
            if 'supportedBy' in json_data:
                actors[json_data['supportedBy']['actorId']] = json_data['supportedBy']
            if 'source' in json_data:
                actors[json_data['source']['actorId']] = json_data['source']

        puid = body_json['puid']
        del body_json['puid']
        format_json = json_files[f'{puid}.json']
        changed = False

        if 'identifierType' in body_json and 'identifierText' in body_json:
            identifiers = format_json['identifiers'] if 'identifiers' in format_json else []
            new_identifier = {
                'identifierText': body_json['identifierText'],
                'identifierType': body_json['identifierType']
            }
            identifiers.append(new_identifier)
            format_json['identifiers'] = identifiers
            changed = True

        if 'relationshipType' in body_json and 'relatedFormatName' in body_json:
            relationships = format_json['relationships'] if 'relationships' in format_json else []
            new_relationship = {
                'relationshipType': body_json['relationshipType'],
                'relatedFormatID': json_files[f'{body_json['relatedFormatName']}.json']['fileFormatID']
            }
            relationships.append(new_relationship)
            format_json['relationships'] = relationships
            changed = True

        def update_actor(field_name):
            next_actor_id = max(actors.keys()) + 1

            existing_value = format_json.get(field_name)
            body_value = body_json.get(field_name)
            if body_value != '0':
                if existing_value is None or existing_value['actorId'] != int(body_value):
                    format_json[field_name] = actors[int(body_value)]
                    return True
            else:
                actor = {'actorId': next_actor_id}

                def add_if_not_empty(key, suffix):
                    if f'{field_name}{suffix}' in body_json:
                        actor[key] = body_json[f'{field_name}{suffix}']

                add_if_not_empty('name', 'Name')
                add_if_not_empty('address', 'Address')
                add_if_not_empty('country', 'Country')
                add_if_not_empty('companyWebsite', 'Company Website')
                add_if_not_empty('supportWebsite', 'Support Website')
                if len(actor) > 1:
                    format_json[field_name] = actor
                    actors[next_actor_id] = actor
                    return True
            return False

        supported_by_updated = update_actor('supportedBy')
        developed_by_updated = update_actor('developedBy')

        for key, value in body_json.items():
            if key in format_json and format_json[key] != body_json[key] and key not in ['supportedBy', 'developedBy']:
                format_json[key] = body_json[key]
                changed = True

        if changed or supported_by_updated or developed_by_updated:
            message = f'Submission to change {puid}'
            path = f'signatures/{puid}.json'
            content_bytes = json.dumps(format_json, indent=2).encode()
            base64_content = base64.b64encode(content_bytes).decode()
            existing_sha = api.repos.get_content(owner, repo, path, branch_name)['sha']
            committer = {'name': tna_name, 'email': tna_email}

            if body_json.get('contributorName') and body_json['contributorName'] != '':
                author_name = body_json['contributorName']
            else:
                author_name = 'The National Archives'
            api.repos.create_or_update_file_contents(
                owner=owner,
                repo=repo,
                message=message,
                path=path,
                committer=committer,
                author={'name': author_name, 'email': tna_email},
                content=base64_content,
                branch=branch_name,
                sha=existing_sha
            )
            head = f'{owner}:{branch_name}'
            base = 'develop'
            body_text = body_json['changeDescription'] if 'changeDescription' in body_json else message
            res = api.pulls.create(parent_owner, repo, message, head=head, base=base, body=body_text)
            print(res)
        else:
            print("Not changed")
