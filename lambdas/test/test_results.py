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
        cursor.execute("DROP TABLE IF EXISTS formats")
        cursor.execute("DROP TABLE IF EXISTS extensions")
        cursor.execute("CREATE TABLE formats (id, path, name, field)")
        cursor.execute("CREATE TABLE extensions (name, format_id)")
        insert_sql = (
            "INSERT INTO formats (id, path, name, field) VALUES (?, ?, ?, ?)"
        )
        for i in range(1, 1001):
            cursor.execute(
                insert_sql,
                (str(i), f"fmt/{i}", f"Test Name {i}", "testsearchstring"),
            )
            cursor.execute("INSERT INTO extensions (name, format_id) VALUES (?, ?)", (f"ext{i}", str(i)))
        conn.commit()

    def tearDown(self):
        os.remove(db_name)

    def test_search_found(self):
        response = results.lambda_handler(
            {"queryStringParameters": {"q": "search"}}, None
        )
        for i in range(1, 1001):
            self.assertTrue(
                f'<a href="fmt/{i}" class="tna-card__heading-link">Test Name {i}</a>'
                in response["body"]
            )
            self.assertTrue(f"<dd>ext{i}</dd>" in response["body"])


    def test_search_not_found(self):
        response = results.lambda_handler(
            {"queryStringParameters": {"q": "invalid"}}, None
        )
        self.assertTrue(
            '<h2 class="tna-heading-m">No results found</h2>' in response["body"]
        )

    def test_search_file_extension(self):
        response = results.lambda_handler(
            {"queryStringParameters": {"q": ".ext1"}}, None
        )
        self.assertEqual(response["statusCode"], 200)
        self.assertTrue(f"<dd>ext1</dd>" in response["body"])


    def test_search_existing_fmt(self):
        response = results.lambda_handler(
            {"queryStringParameters": {"q": "fmt/123"}}, None
        )
        self.assertEqual(response["statusCode"], 302)
        self.assertEqual(response["headers"]["Location"], "fmt/123")

    def test_search_existing_fmt_upper_case(self):
        response = results.lambda_handler(
            {"queryStringParameters": {"q": "FMT/123"}}, None
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
