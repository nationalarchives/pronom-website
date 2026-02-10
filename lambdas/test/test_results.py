import os
import sqlite3
import unittest
from unittest import mock

from lambdas.results import results

db_name = "test_indexes"


@mock.patch.dict(os.environ, {"DB_NAME": db_name})
class ResultsTest(unittest.TestCase):

    def setUp(self):
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS indexes")
        cursor.execute("CREATE TABLE indexes (path, name, field)")
        insert_sql = "INSERT INTO indexes (path, name, field) VALUES (?, ?, ?)"
        for i in range(1, 1001):
            cursor.execute(
                insert_sql,
                (f"fmt/{i}", f"Test Name {i}", "testsearchstring"),
            )
        conn.commit()

    def tearDown(self):
        os.remove(db_name)


    def test_search_found(self):
        response = results.lambda_handler(
            {"queryStringParameters": {"q": "search"}}, None
        )
        self.assertTrue('<td class="tna-table__cell"><a href="fmt/1">fmt/1</a></td>' in response["body"])



    def test_search_not_found(self):
        response = results.lambda_handler(
            {"queryStringParameters": {"q": "invalid"}}, None
        )
        self.assertTrue(
            '<h3 class="tna-heading-m">No results found</h3>' in response["body"]
        )

    def test_search_existing_fmt(self):
        response = results.lambda_handler(
            {"queryStringParameters": {"q": "fmt/123"}}, None
        )
        self.assertEqual(response["statusCode"], 302)
        self.assertEqual(response["headers"]["Location"], "fmt/123")

    def test_search_not_existing_fmt(self):
        response = results.lambda_handler(
            {"queryStringParameters": {"q": "fmt/3210"}}, None
        )
        self.assertTrue(
            '<h3 class="tna-heading-m">No results found</h3>' in response["body"]
        )
