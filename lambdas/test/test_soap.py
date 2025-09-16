import os
import unittest
from unittest.mock import Mock, mock_open, patch

from lambdas.soap import soap


class SoapTest(unittest.TestCase):

    @staticmethod
    def open_mock_file(file, *args, **kwargs):
        if file == 'version':
            return mock_open(read_data='Test version file content').return_value
        elif file == 'soap_description.html':
            return mock_open(read_data='Test soap description').return_value
        elif file == 'signature_file_description.html':
            return mock_open(read_data='Test signature file description').return_value
        elif file == 'signature_file_version_description.html':
            return mock_open(read_data='Test signature file version description').return_value
        else:
            return mock_open(read_data='Test wsdl').return_value

    def test_return_404_if_header_missing(self):
        response = soap.lambda_handler({'httpMethod': 'POST', 'headers': {}}, None)
        self.assertEqual(response['statusCode'], 404)

    def test_return_404_if_header_invalid(self):
        response = soap.lambda_handler({'httpMethod': 'POST', 'headers': {'soapaction': 'invalid'}}, None)
        self.assertEqual(response['statusCode'], 404)

    @patch("urllib.request.urlopen")
    def test_return_downloaded_file(self, mock_urlopen):
        os.environ["DOWNLOAD_URL"] = "http://example.com/test"
        mock_response = Mock()
        mock_response.read.return_value = b"Test String"
        mock_urlopen.return_value = mock_response
        action = 'http://pronom.nationalarchives.gov.uk:getSignatureFileV1In'
        response = soap.lambda_handler({'httpMethod': 'POST', 'headers': {'soapaction': action}}, None)

        expected_body = '''<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <soap:Body>
    <getSignatureFileV1Response xmlns="http://pronom.nationalarchives.gov.uk">
      <SignatureFile>
Test String
      </SignatureFile>
    </getSignatureFileV1Response>
  </soap:Body>
</soap:Envelope>
'''
        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(response['body'], expected_body)
        self.assertEqual(response['headers']['Content-Type'], 'text/xml')

    @patch('builtins.open', side_effect=open_mock_file)
    def test_return_version_file(self, _):
        action = 'http://pronom.nationalarchives.gov.uk:getSignatureFileVersionV1In'
        response = soap.lambda_handler({'httpMethod': 'POST', 'headers': {'soapaction': action}}, None)
        self.assertEqual(response['body'], 'Test version file content')
        self.assertEqual(response['headers']['Content-Type'], 'text/xml')
        self.assertEqual(response['statusCode'], 200)

    @patch('builtins.open', side_effect=open_mock_file)
    def test_return_soap_description(self, _):
        response = soap.lambda_handler({'httpMethod': 'GET'}, None)
        self.assertEqual(response['body'], 'Test soap description')
        self.assertEqual(response['headers']['Content-Type'], 'text/html')
        self.assertEqual(response['statusCode'], 200)

    @patch('builtins.open', side_effect=open_mock_file)
    def test_return_signature_file_description(self, _):
        event = {'httpMethod': 'GET', 'queryStringParameters': {'op': 'getSignatureFileV1'}}
        response = soap.lambda_handler(event, None)
        self.assertEqual(response['body'], 'Test signature file description')
        self.assertEqual(response['headers']['Content-Type'], 'text/html')
        self.assertEqual(response['statusCode'], 200)

    @patch('builtins.open', side_effect=open_mock_file)
    def test_return_signature_file_version_description(self, _):
        event = {'httpMethod': 'GET', 'queryStringParameters': {'op': 'getSignatureFileVersionV1'}}
        response = soap.lambda_handler(event, None)
        self.assertEqual(response['body'], 'Test signature file version description')
        self.assertEqual(response['headers']['Content-Type'], 'text/html')
        self.assertEqual(response['statusCode'], 200)

    @patch('builtins.open', side_effect=open_mock_file)
    def test_return_wsdl(self, _):
        event = {'httpMethod': 'GET', 'queryStringParameters': {'WSDL': ''}}
        response = soap.lambda_handler(event, None)
        self.assertEqual(response['body'], 'Test wsdl')
        self.assertEqual(response['headers']['Content-Type'], 'text/xml')
        self.assertEqual(response['statusCode'], 200)
