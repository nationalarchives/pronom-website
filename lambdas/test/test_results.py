import unittest
import sqlite3
from lambdas import results
import os


class ResultsTest(unittest.TestCase):

    def setUp(self):
        conn = sqlite3.connect("indexes")
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS indexes")
        cursor.execute("CREATE TABLE indexes (path, name, field)")
        insert_sql = "INSERT INTO indexes (path, name, field) VALUES (?, ?, ?)"
        cursor.execute(insert_sql, ('fmt/123', 'Test Name', 'testsearchstring'), )
        conn.commit()

    def tearDown(self):
        os.remove("indexes")

    def test_search_found(self):
        response = results.lambda_handler({'queryStringParameters': {'q': 'search'}}, None)
        self.assertTrue('<dt><a href="fmt/123">fmt/123</a></dt>' in response['body'])

    def test_search_not_found(self):
        response = results.lambda_handler({'queryStringParameters': {'q': 'invalid'}}, None)
        self.assertTrue('<p class="tna-large-paragraph">No results found</p>' in response['body'])

    def test_search_existing_fmt(self):
        response = results.lambda_handler({'queryStringParameters': {'q': 'fmt/123'}}, None)
        self.assertEqual(response['statusCode'], 302)
        self.assertEqual(response['headers']['Location'], 'fmt/123')

    def test_search_not_existing_fmt(self):
        response = results.lambda_handler({'queryStringParameters': {'q': 'fmt/321'}}, None)
        self.assertTrue('<p class="tna-large-paragraph">No results found</p>' in response['body'])


if __name__ == '__main__':
    unittest.main()