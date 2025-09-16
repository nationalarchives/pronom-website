import urllib.request
import os


def response(contents, content_type='xml'):
    return {
        'statusCode': 200,
        'body': contents,
        "headers": {"Content-Type": f"text/{content_type}"}
    }


def file_response(file_name):
    with open(file_name) as file_contents:
        content_type = file_name.split(".")[1]
        return response(file_contents.read(), content_type)


soap_response_prefix = '''<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <soap:Body>
    <getSignatureFileV1Response xmlns="http://pronom.nationalarchives.gov.uk">
      <SignatureFile>
'''

soap_response_suffix = '''
      </SignatureFile>
    </getSignatureFileV1Response>
  </soap:Body>
</soap:Envelope>
'''


def lambda_handler(event, context):
    print(event)
    method = event['httpMethod']
    if method == 'GET':
        if 'queryStringParameters' in event and event['queryStringParameters']:
            query_params = {key.lower(): value.lower() for key, value in event['queryStringParameters'].items()}
            if 'wsdl' in query_params:
                return file_response("soap_wsdl.xml")
            if 'op' in query_params:
                if query_params['op'] == 'getsignaturefilev1':
                    return file_response("signature_file_description.html")
                if query_params['op'] == 'getsignaturefileversionv1':
                    return file_response("signature_file_version_description.html")
        else:
            return file_response("soap_description.html")
    else:
        headers = event['headers']
        if 'soapaction' not in headers:
            return {'statusCode': 404}
        action = headers['soapaction']
        if "http://pronom.nationalarchives.gov.uk:getSignatureFileVersionV1In" in action:
            with open("version") as version_file:
                return response(version_file.read())
        elif "http://pronom.nationalarchives.gov.uk:getSignatureFileV1In" in action:
            ff_signature_xml = urllib.request.urlopen(os.environ['DOWNLOAD_URL']).read().decode("utf-8")
            xml_without_declaration = ff_signature_xml.replace('<?xml version="1.0" encoding="UTF-8"?>', '')
            response_xml = soap_response_prefix + xml_without_declaration + soap_response_suffix
            print(len(response_xml))
            return response(response_xml)
        else:
            return {'statusCode': 404}
