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
    return {
        'Name': data['formatName'],
        'Version': data['version'] if 'version' in data else '',
        'Identifiers': identifiers,
        'Family': data['formatFamilies'] if 'formatFamilies' in data else '',
        'Disclosure': data['formatDisclosure'] if 'formatDisclosure' in data else '',
        'Description': data['formatDescription'] if 'formatDescription' in data else '',
        'Source': data['provenanceCompoundName'] if 'provenanceCompoundName' in data else '',
        'Note': data['formatNote'] if 'formatNote' in data else ''
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


def create_detail(json_path):
    with open(json_path, 'r') as sig_json:
        data = json.load(sig_json)
        index_template = env.get_template("index.html")
        details_template = env.get_template("details.html")
        summary = get_summary(data)
        signatures = get_signatures(data)
        summary_section = env.get_template("details_section.html").render(title="Summary", results=[summary], open=True)
        signatures_section = env.get_template("details_section.html").render(title="Signatures", results=signatures)
        content = details_template.render(name=summary['Name'], summary=summary_section,
                                          signatures=signatures_section)
        return index_template.render(content=content)


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
    with open('site/signature_list.html', 'w') as signature_list:
        signature_list.write(create_file_list())

    with open('site/home.html', 'w') as home:
        home.write(create_home())

    with open('site/search.html', 'w') as search:
        search.write(create_search())

    for sub_dir in ['fmt', 'x-fmt']:
        sig_files = os.listdir(f'{path}/signatures/{sub_dir}')
        for file in sig_files:
            with open(f'site/{sub_dir}/{file.split(".")[0]}.html', 'w') as output:
                output.write(create_detail(f'{path}/signatures/{sub_dir}/{file}'))


run()
