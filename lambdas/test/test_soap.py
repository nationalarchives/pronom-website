import os
import unittest
from unittest.mock import patch, Mock, mock_open

from lambdas import soap


class SoapTest(unittest.TestCase):

    def test_return_404_if_header_missing(self):
        response = soap.lambda_handler({'headers': {}}, None)
        self.assertEqual(response['statusCode'], 404)

    def test_return_404_if_header_invalid(self):
        response = soap.lambda_handler({'headers': {'soapaction': 'invalid'}}, None)
        self.assertEqual(response['statusCode'], 404)

    @patch('urllib.request.urlopen')
    def test_return_downloaded_file(self, mock_urlopen):
        os.environ['DOWNLOAD_URL'] = 'http://example.com/test'
        mock_response = Mock()
        mock_response.read.return_value = b'Test String'
        mock_urlopen.return_value = mock_response
        action = 'http://pronom.nationalarchives.gov.uk:getSignatureFileV1In'
        response = soap.lambda_handler({'headers': {'soapaction': action}}, None)
        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(response['body'], b'Test String')
        self.assertEqual(response['headers']['Content-Type'], 'text/xml')

    @patch('builtins.open', new_callable=mock_open, read_data='Test file content')
    def test_return_version_file(self, mock_file):
        action = 'http://pronom.nationalarchives.gov.uk:getSignatureFileVersionV1In'
        response = soap.lambda_handler({'headers': {'soapaction': action}}, None)
        self.assertEqual(response['body'], 'Test file content')
        self.assertEqual(response['headers']['Content-Type'], 'text/xml')
        self.assertEqual(response['statusCode'], 200)
