import os
import re
import sys
import json
from urllib import request

from jinja2 import Environment, ChoiceLoader, PackageLoader, FileSystemLoader, select_autoescape
from datetime import datetime
import pycountry

template_dir = "./lambdas/templates"
env = Environment(
    loader=ChoiceLoader([FileSystemLoader(template_dir), PackageLoader("tna_frontend_jinja"), ]),
    autoescape=select_autoescape()
)

bucket_name = 'tna-pronom-signatures-spike'


def render_index(content):
    with open(f'{template_dir}/site.js') as js_file:
        index_template = env.get_template("index.html")
        return index_template.render(js=js_file.read(), content=content)


def get_summary(data):
    identifiers = ', '.join(
        [f"{identifier['identifierType']}: {identifier['identifierText']}" for identifier in data['identifiers']]
    )

    def str_for_attr(attr): return data[attr] if attr in data and data[attr] is not None else ''

    return {
        'Name': str_for_attr('formatName'),
        'Version': str_for_attr('version'),
        'Identifiers': identifiers,
        'Format Type': str_for_attr('formatTypes'),
        'Family': str_for_attr('formatFamilies'),
        'Disclosure': str_for_attr('formatDisclosure'),
        'Description': str_for_attr('formatDescription'),
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


def create_modify_page(puid, json_data, actor_select, json_by_id):
    def str_for_attr(attr):
        return json_data[attr] if attr in json_data and json_data[attr] is not None else ''

    identifier_type_names = ['PUID', 'Other', 'GDFR Format Identifier', 'MIME', 'TOM Identifier', 'GDFRClass',
                             'GDFRRegistry', 'URL', 'Apple Uniform Type Identifier',
                             'Library of Congress Format Description Identifier', 'Wikidata QID Identifier']
    relationship_type_names = ['Other', 'Is subsequent version of', 'Is previous version of', 'Is subtype of',
                               'Is supertype of', 'Can contain', 'Can be contained by', 'Has priority over',
                               'Equivalent to']

    def get_types(type_names):
        types = sorted([{'text': x, 'value': x} for x in type_names], key=lambda x: x['text'])
        types.insert(0, {'text': '', 'value': ''})
        return types

    relationship_types = get_types(relationship_type_names)
    identifier_types = get_types(identifier_type_names)

    relationships = []
    if 'relationships' in json_data:
        for relationship in json_data['relationships']:
            related_format = json_by_id[relationship['relatedFormatID']]
            relationship_type = relationship['relationshipType']
            relationships.append({'puid': related_format, 'type': relationship_type})

    modify_data = {
        "name": str_for_attr("formatName"),
        "families": str_for_attr("formatFamilies"),
        "disclosure": str_for_attr("formatDisclosure"),
        "description": str_for_attr("formatDescription"),
        "formatTypes": str_for_attr("formatTypes"),
        "identifiers": json_data['identifiers'] if 'identifiers' in json_data else [],
        "relationships": relationships,
        "identifierTypes": identifier_types,
        "relationshipTypes": relationship_types,
        "source": str_for_attr("provenanceCompoundName"),
        "note": str_for_attr("formatNote"),
        "developedBy": json_data["developedBy"] if "developedBy" in json_data else 0,
        "supportedBy": json_data["supportedBy"] if "supportedBy" in json_data else 0
    }
    signature = None
    change_type = 'edit'
    if puid:
        modify_data['puid'] = puid
    else:
        change_type = 'add'
        signature = create_signature_section()
    modify = env.get_template("modify.html")

    return modify.render(result=modify_data, actors=actor_select, change_type=change_type, signature=signature)


def create_countries_select():
    def get_countries():
        return [{'text': country.name, 'value': country.name} for country in pycountry.countries]

    countries = sorted(get_countries(), key=lambda x: x['text'])
    countries.insert(0, {'text': '', 'value': ''})
    return countries


def create_add_actor():
    add_actor_template = env.get_template("modify_actor.html")
    countries = create_countries_select()
    actor = {'name': '', 'address': '', 'addressCountry': '', 'supportWebsite': '', 'companyWebsite': ''}
    return add_actor_template.render(countries=countries, change_type='add', actor=actor)


def create_edit_actor(actor):
    add_actor_template = env.get_template("modify_actor.html")
    countries = create_countries_select()
    return add_actor_template.render(countries=countries, change_type='edit', actor=actor)


def create_detail(puid, json_data, all_actors):
    details_template = env.get_template("details.html")
    summary = get_summary(json_data)
    signatures = get_signatures(json_data)
    summary_args = {
        "id": "summary",
        "title": "Summary",
        "results": [summary],
        "open": True,
        "developedBy": all_actors[json_data['developedBy']] if 'developedBy' in json_data else None,
        "supportedBy": all_actors[json_data['supportedBy']] if 'supportedBy' in json_data else None,
        "source": all_actors[json_data['source']] if 'source' in json_data else None
    }
    signatures_args = {"title": "Signatures", "results": signatures, "id": "signatures"}
    summary_section = env.get_template("details_section.html").render(**summary_args)
    signatures_section = env.get_template("details_section.html").render(**signatures_args)
    container_template = env.get_template("container_signature_section.html")
    container_content = container_template.render(data=json_data)
    edit_path = f'/edit/{puid}'
    content = details_template.render(name=summary['Name'], summary=summary_section,
                                      signatures=signatures_section, containers=container_content, editPath=edit_path)
    return render_index(content=content)


def create_actor(data):
    def format_date(): return datetime.strptime(data['sourceDate'], "%Y-%m-%d").strftime("%d %b %Y")

    return {
        'Address': data['address'] if 'address' in data else '',
        'Country': data['addressCountry'] if 'addressCountry' in data else '',
        'Support Website': data['supportWebsite'] if 'supportWebsite' in data else '',
        'Company Website': data['companyWebsite'] if 'companyWebsite' in data else '',
        'Contact': data['contact'] if 'contact' in data else '',
        'Source': data['source'] if 'source' in data else '',
        'Source Date': format_date() if 'sourceDate' in data else ''
    }


def create_signature_section():
    position_type_names = ['Absolute from BOF', 'Absolute from EOF', 'Variable', 'Indirect From BOF',
                           'Indirect From EOF']
    position_type_select = [{'value': x, 'text': x} for x in position_type_names]
    position_type_select.insert(0, {'value': '', 'text': ''})
    signature_template = env.get_template('signature.html')
    return signature_template.render(position_types=position_type_select)


def create_home():
    home_template = env.get_template("home.html")
    return render_index(home_template.render())


def create_search():
    search_template = env.get_template("search.html")
    return render_index(search_template.render())


path = sys.argv[1]


def create_file_list():
    with request.urlopen("https://d21gi86t6uhf68.cloudfront.net/signatures.json") as url:
        all_signatures = json.load(url)

    signatures = sorted(all_signatures['signatures'], key=lambda k: int(re.search(r'(\d+)', k["location"]).group(1)))
    container_signatures = all_signatures["container_signatures"]

    signature_list_template = env.get_template("signature_list.html")
    signature_list_content = (
        signature_list_template.render(signature_data=signatures, container_signature_data=container_signatures))
    return render_index(signature_list_content)


def run():
    with open('site/signature_list', 'w') as signature_list:
        signature_list.write(create_file_list())

    with open('site/home', 'w') as home:
        home.write(create_home())

    with open('site/search', 'w') as search:
        search.write(create_search())

    all_json_files = {}
    all_actors = {}
    json_by_id = {}

    for file in os.listdir(f'{path}/actors'):
        with open(f'{path}/actors/{file}') as actor_file:
            actor_json = json.load(actor_file)
            actor_id = actor_json['actorId']
            all_actors[actor_id] = actor_json

    for sub_dir in ['fmt', 'x-fmt']:
        sig_files = os.listdir(f'{path}/signatures/{sub_dir}')
        for file in sig_files:
            json_path = f'{path}/signatures/{sub_dir}/{file}'
            with open(json_path, 'r') as sig_json:
                puid = f'{sub_dir}/{file.split(".")[0]}'
                loaded_json = json.load(sig_json)
                all_json_files[puid] = loaded_json
                json_by_id[loaded_json['fileFormatID']] = puid

    actor_select = [{'text': '', 'value': 0}]
    for actor_json in all_actors.values():
        actor_select.append({'text': actor_json['name'], 'value': actor_json['actorId']})

    actor_select = sorted(actor_select, key=lambda x: x['text'])

    for puid, json_data in all_json_files.items():
        with open(f'site/{puid}', 'w') as output, open(f'site/edit/{puid}', 'w') as edit_page:
            output.write(create_detail(puid, json_data, all_actors))
            edit_content = create_modify_page(puid, json_data, actor_select, json_by_id)
            edit_page.write(render_index(edit_content))

    with open('site/add', 'w') as add_page:
        add_page.write(render_index(create_modify_page(None, {}, actor_select, {})))

    for actor_json in all_actors.values():
        actor_id = actor_json['actorId']
        view_path = f'site/actor/{actor_id}'
        edit_path = f'site/actor/edit/{actor_id}'
        with open(view_path, 'w') as actor_page, open(edit_path, 'w') as edit_actor_page:
            actor_details_template = env.get_template("actor_details.html")
            actor = create_actor(actor_json)
            name = actor_json['name']
            actor_details = actor_details_template.render(results=actor, name=name, actorId=actor_id)
            actor_page.write(render_index(actor_details))
            edit_actor_page.write(render_index(create_edit_actor(actor_json)))

    with open('site/actor/add', 'w') as add_actor_page, open('site/contribute', 'w') as contribute_page:
        contribute_page_template = env.get_template('contribute.html')
        add_actor_page.write(render_index(create_add_actor()))
        contribute_page.write(render_index(contribute_page_template.render()))


run()
