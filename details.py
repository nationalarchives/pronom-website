from utils import *
import boto3
import json


def get_summary(data):
    format_detail = data['formatDetail'][0]
    identifiers = ', '.join(
        [f"{identifier['identifierType']}: {identifier['identifierText']}" for identifier in data['formatIdentifiers']]
    )
    return {
        'Name': format_detail['formatName'],
        'Version': format_detail['version'],
        'Identifiers': identifiers,
        'Family': format_detail['formatFamilies'],
        'Disclosure': format_detail['formatDisclosure'],
        'Description': format_detail['formatDescription'],
        'Supported by': ', '.join([support['organisationName'] for support in data['formatSupport']]),
        'Source': format_detail['provenanceCompoundName'],
        'Note': format_detail['formatNote']
    }


def get_signatures(data):
    if len(data['formatInternalSignatures']) == 1:
        format_internal_signatures = data['formatInternalSignatures'][0]
        byte_sequences = data['formatIntSigByteSequences'][0]
        return {
            'Name': format_internal_signatures['signatureName'],
            'Description': format_internal_signatures['signatureNote'],
            'Position Type': byte_sequences['positionType'],
            'Offset': byte_sequences['offset'],
            'Maximum offset': byte_sequences['maxOffset'],
            'Value': byte_sequences['byteSequence']
        }
    else:
        return {}


def read_json_from_s3(file_key):
    s3_client = boto3.client('s3')
    bucket_name = 'tna-pronom-signatures-spike'

    response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
    content = response['Body'].read().decode('utf-8')
    json_data = json.loads(content)
    return json_data


def lambda_handler(event, _):
    def create_body(_):
        params = event['pathParameters']
        json_path = f"{params['prefix']}/{params['id']}.json"
        index_template = env.get_template("index.html")
        details_template = env.get_template("details.html")
        data = read_json_from_s3(json_path)
        summary = get_summary(data)
        signatures = get_signatures(data)
        summary_section = env.get_template("details_section.html").render(title="Summary", data=summary, open=True)
        signatures_section = env.get_template("details_section.html").render(title="Signatures", data=signatures)
        content = details_template.render(name=summary['Name'], summary=summary_section,
                                          signatures=signatures_section)
        return index_template.render(content=content)

    return handler(event, create_body)
