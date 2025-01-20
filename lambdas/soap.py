import urllib.request
import os


def response(contents):
    return {
        'statusCode': 200,
        'body': contents,
        "headers": {"Content-Type": "text/xml"}
    }


def lambda_handler(event, context):
    headers = event['headers']
    if 'soapaction' not in headers:
        return {'statusCode': 404}
    action = headers['soapaction']
    if action == "http://pronom.nationalarchives.gov.uk:getSignatureFileVersionV1In":
        with open("version") as version_file:
            return response(version_file.read())
    elif action == "http://pronom.nationalarchives.gov.uk:getSignatureFileV1In":
        contents = urllib.request.urlopen(os.environ['DOWNLOAD_URL']).read()
        return response(contents)
    else:
        return {'statusCode': 404}
