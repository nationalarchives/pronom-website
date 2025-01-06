from jinja2 import Environment, ChoiceLoader, PackageLoader, FileSystemLoader, select_autoescape
import sqlite3
import re

env = Environment(
    loader=ChoiceLoader([FileSystemLoader("./templates"), PackageLoader("tna_frontend_jinja"), ]),
    autoescape=select_autoescape()
)


def puid_exists(puid):
    conn = sqlite3.connect("indexes")
    cursor = conn.cursor()
    cursor.execute("SELECT path from indexes where path = ?", (puid,))
    rows = cursor.fetchall()
    return len(rows) > 0


def search(search_string):
    conn = sqlite3.connect('indexes')
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
    index_template = env.get_template("index.html")
    search_results = env.get_template("search_results.html")
    content = search_results.render(data=data)
    body = index_template.render(content=content)

    try:
        return {
            "statusCode": 200,
            "body": body,
            "headers": {"Content-Type": "text/html"}
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": f"An error occurred: {str(e)}",
            "headers": {
                "Content-Type": "text/html"
            }
        }
