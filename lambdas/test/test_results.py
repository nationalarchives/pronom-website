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
        cursor.execute("CREATE TABLE indexes (path, name, extensions, field)")
        insert_sql = (
            "INSERT INTO indexes (path, name, extensions, field) VALUES (?, ?, ?, ?)"
        )
        for i in range(1, 1001):
            cursor.execute(
                insert_sql,
                (f"fmt/{i}", f"Test Name {i}", f"ext{i}", "testsearchstring"),
            )
        conn.commit()

    def tearDown(self):
        os.remove(db_name)

    def test_search_found(self):
        response = results.lambda_handler(
            {"queryStringParameters": {"q": "search"}}, None
        )
        for i in range(1, 1001):
            self.assertTrue(
                f'<thd class="tna-table__header"><a href="fmt/{i}">fmt/{i}</a></th>'
                in response["body"]
            )
            self.assertTrue(
                f'<td class="tna-table__cell">ext{i}</td>' in response["body"]
            )
            self.assertTrue(
                f'<td class="tna-table__cell">Test Name {i}</td>' in response["body"]
            )

    def test_search_not_found(self):
        response = results.lambda_handler(
            {"queryStringParameters": {"q": "invalid"}}, None
        )
        self.assertTrue(
            '<h2 class="tna-heading-m">No results found</h2>' in response["body"]
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
            '<h2 class="tna-heading-m">No results found</h2>' in response["body"]
        )
