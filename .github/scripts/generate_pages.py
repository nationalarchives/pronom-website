import os
import re
import sys
import boto3
import json
from jinja2 import Environment, ChoiceLoader, PackageLoader, FileSystemLoader, select_autoescape
from datetime import datetime

env = Environment(
    loader=ChoiceLoader([FileSystemLoader("templates"), PackageLoader("tna_frontend_jinja"), ]),
    autoescape=select_autoescape()
)

bucket_name = 'tna-pronom-signatures-spike'


def get_summary(data):
    identifiers = ', '.join(
        [f"{identifier['identifierType']}: {identifier['identifierText']}" for identifier in data['identifiers']]
    )

    def str_for_attr(attr): return data[attr] if attr in data and data[attr] is not None else ''

    return {
        'Name': str_for_attr('formatName'),
        'Version': str_for_attr('version'),
        'Identifiers': identifiers,
        'Family': str_for_attr('formatFamilies'),
        'Disclosure': str_for_attr('formatDisclosure'),
        'Description': str_for_attr('formatDescription'),
        'Source': str_for_attr('provenanceCompoundName'),
        'Note': str_for_attr('formatNote')
    }


def get_signatures(data):
    def process_signature(internal_signature):
        return {
            'Name': internal_signature['name'],
            'Description': internal_signature['note'],
            'Position Type': internal_signature['positionType'],
            'Offset': internal_signature['offset'],
            'Maximum offset': internal_signature['maxOffset'],
            'Value': internal_signature['byteSequence']
        }

    return [process_signature(sig) for sig in data['internalSignatures']]


def read_json_from_s3(file_key):
    s3_client = boto3.client('s3')

    response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
    content = response['Body'].read().decode('utf-8')
    json_data = json.loads(content)
    return json_data


def create_edit_page(puid, json_data, actor_select):
    def str_for_attr(attr): return json_data[attr] if attr in json_data and json_data[attr] is not None else ''

    def num_for_attr(attr): return json_data[attr] if attr in json_data and json_data[attr] is not None else 0

    edit_data = {
        "puid": puid,
        "name": str_for_attr("formatName"),
        "families": str_for_attr("formatFamilies"),
        "disclosure": str_for_attr("formatDisclosure"),
        "description": str_for_attr("formatDescription"),
        "source": str_for_attr("provenanceCompoundName"),
        "note": str_for_attr("formatNote"),
        "developedBy": json_data["developedBy"]['actorId'] if "developedBy" in json_data else 0,
        "supportedBy": json_data["supportedBy"]['actorId'] if "supportedBy" in json_data else 0
    }
    edit_template = env.get_template("edit.html")
    return edit_template.render(result=edit_data, actors=actor_select)


def create_detail(puid, json_data):
    index_template = env.get_template("index.html")
    details_template = env.get_template("details.html")
    summary = get_summary(json_data)
    signatures = get_signatures(json_data)
    summary_args = {
        "id": "summary",
        "title": "Summary",
        "results": [summary],
        "open": True,
        "developedBy": json_data['developedBy'] if 'developedBy' in json_data else None,
        "supportedBy": json_data['supportedBy'] if 'supportedBy' in json_data else None
    }
    signatures_args = {"title": "Signatures", "results": signatures, "id": "signatures"}
    summary_section = env.get_template("details_section.html").render(**summary_args)
    signatures_section = env.get_template("details_section.html").render(**signatures_args)
    container_template = env.get_template("container_signature_section.html")
    container_content = container_template.render(data=json_data)
    edit_path = f'/edit/{puid}'
    content = details_template.render(name=summary['Name'], summary=summary_section,
                                      signatures=signatures_section, containers=container_content, editPath=edit_path)
    return index_template.render(content=content)


def create_actor(data):
    def format_date(): return datetime.strptime(data['sourceDate'], "%Y-%m-%d").strftime("%d %b %Y")

    return {
        'Address': data['address'] if 'version' in data else '',
        'Country': data['country'] if 'country' in data else '',
        'Support Website': data['supportWebsite'] if 'supportWebsite' in data else '',
        'Company Website': data['companyWebsite'] if 'companyWebsite' in data else '',
        'Contact': data['contact'] if 'contact' in data else '',
        'Source': data['source'] if 'source' in data else '',
        'Source Date': format_date() if 'sourceDate' in data else ''
    }


def create_home():
    home_template = env.get_template("home.html")
    index_template = env.get_template("index.html")
    return index_template.render(content=home_template.render())


def create_search():
    index_template = env.get_template("index.html")
    search_template = env.get_template("search.html")
    return index_template.render(content=search_template.render())


path = sys.argv[1]


def create_file_list():
    client = boto3.client('s3')

    def list_keys(prefix):
        return [obj['Key'] for obj in client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)['Contents']]

    def signature_key_to_name(key):
        version = key.split('_')[2].split('.')[0]
        return f'DROID Signature File {version}'

    def container_key_to_name(key):
        date_str = key.split('-')[3].split('.')[0]
        date_obj = datetime.strptime(date_str, "%Y%m%d")
        return date_obj.strftime("%d %B %Y")

    signatures = sorted(list_keys('signatures'), key=lambda k: int(re.search(r'(\d+)', k).group(1)))
    container_signatures = list_keys('container-signatures')
    signature_map = [{'name': signature_key_to_name(key), 'href': key} for key in signatures]
    container_signature_map = [{'name': container_key_to_name(key), 'href': key} for key in container_signatures]

    index_template = env.get_template("index.html")
    signature_list_template = env.get_template("signature_list.html")
    signature_list_content = (
        signature_list_template.render(signature_data=signature_map, container_signature_data=container_signature_map))
    return index_template.render(content=signature_list_content)


def run():
    with open('site/signature_list', 'w') as signature_list:
        signature_list.write(create_file_list())

    with open('site/home', 'w') as home:
        home.write(create_home())

    with open('site/search', 'w') as search:
        search.write(create_search())

    all_json_files = {}
    index_template = env.get_template("index.html")

    for sub_dir in ['fmt', 'x-fmt']:
        sig_files = os.listdir(f'{path}/signatures/{sub_dir}')
        for file in sig_files:
            json_path = f'{path}/signatures/{sub_dir}/{file}'
            with open(json_path, 'r') as sig_json:
                all_json_files[f'{sub_dir}/{file.split(".")[0]}'] = json.load(sig_json)

    actors = {}
    for json_data in all_json_files.values():
        if 'developedBy' in json_data:
            actors[json_data['developedBy']['actorId']] = json_data['developedBy']
        if 'supportedBy' in json_data:
            actors[json_data['supportedBy']['actorId']] = json_data['supportedBy']

    actor_select = [{'text': '', 'value': 0}]
    for actor_json in actors.values():
        actor_select.append({'text': actor_json['name'], 'value': actor_json['actorId']})

    actor_select = sorted(actor_select, key=lambda x: x['text'])

    for puid, json_data in all_json_files.items():
        with open(f'site/{puid}', 'w') as output, open(f'site/edit/{puid}', 'w') as edit_page:
            output.write(create_detail(puid, json_data))
            edit_page.write(index_template.render(content=create_edit_page(puid, json_data, actor_select)))

    for actor_json in actors.values():
        with open(f'site/actor/{actor_json['actorId']}', 'w') as actor_page:
            actor_details_template = env.get_template("actor_details.html")
            actor_details = actor_details_template.render(results=create_actor(actor_json), name=actor_json['name'])
            actor_page.write(index_template.render(content=actor_details))

    submissions_received_template = env.get_template("submissions_received.html")
    with open(f'site/submission-received', 'w') as submission_received:
        submission_received.write(index_template.render(content=submissions_received_template.render()))


run()
