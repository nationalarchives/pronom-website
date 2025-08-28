import os

from jinja2 import Environment, ChoiceLoader, PackageLoader, FileSystemLoader, select_autoescape
import sqlite3
import re

env = Environment(
    loader=ChoiceLoader([FileSystemLoader("./lambdas/templates"), PackageLoader("tna_frontend_jinja"), ]),
    autoescape=select_autoescape()
)


def puid_exists(puid):
    db_name = os.getenv("DB_NAME", "indexes")
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("SELECT path from indexes where path = ?", (puid,))
    rows = cursor.fetchall()
    return len(rows) > 0


def search(search_string):
    db_name = os.getenv("DB_NAME", "indexes")
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()
    cur.execute('select path, name from indexes where field like ?', (f"%{search_string}%",))
    rows = cur.fetchall()
    cur.close()
    return rows


def lambda_handler(event, _):
    query_params = event.get("queryStringParameters", {})
    search_term = query_params.get("q") if query_params else None
    if re.search(r'^(x-)?fmt\/\d{1,5}$', search_term) is not None and puid_exists(search_term):
        return {
            "statusCode": 302,
            "headers": {'Location': search_term}
        }
    rows = search(search_term)
    data = {f'{row[0]}': row[1] for row in rows}
    search_results = env.get_template("search_results.html")
    body = search_results.render(data=data, search_term=search_term)

    return {
        "statusCode": 200,
        "body": body,
        "headers": {"Content-Type": "text/html"}
    }
