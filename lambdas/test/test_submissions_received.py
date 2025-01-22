import unittest
from lambdas import submissions_received


class SubmissionsReceivedTest(unittest.TestCase):
    def test_render_submissions_received(self):
        response = submissions_received.lambda_handler({'rawPath': '/1'}, None)
        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(response['headers']['Content-Type'], 'text/html')
        self.assertTrue('nationalarchives/pronom-signatures/pull/1' in response['body'])
