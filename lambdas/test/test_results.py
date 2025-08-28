import unittest
import sqlite3
from unittest import mock

from lambdas import results
import os

db_name = "test_indexes"


@mock.patch.dict(os.environ, {"DB_NAME": db_name})
class ResultsTest(unittest.TestCase):

    def setUp(self):
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS indexes")
        cursor.execute("CREATE TABLE indexes (path, name, field)")
        insert_sql = "INSERT INTO indexes (path, name, field) VALUES (?, ?, ?)"
        cursor.execute(insert_sql, ('fmt/123', 'Test Name', 'testsearchstring'), )
        conn.commit()

    def tearDown(self):
        os.remove(db_name)

    def test_search_found(self):
        response = results.lambda_handler({'queryStringParameters': {'q': 'search'}}, None)
        self.assertTrue('<dt><a href="fmt/123">fmt/123</a></dt>' in response['body'])

    def test_search_not_found(self):
        response = results.lambda_handler({'queryStringParameters': {'q': 'invalid'}}, None)
        self.assertTrue('<h1 class="tna-heading-xl">No results found</h1>' in response['body'])

    def test_search_existing_fmt(self):
        response = results.lambda_handler({'queryStringParameters': {'q': 'fmt/123'}}, None)
        self.assertEqual(response['statusCode'], 302)
        self.assertEqual(response['headers']['Location'], 'fmt/123')

    def test_search_not_existing_fmt(self):
        response = results.lambda_handler({'queryStringParameters': {'q': 'fmt/321'}}, None)
        self.assertTrue('<h1 class="tna-heading-xl">No results found</h1>' in response['body'])
