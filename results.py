from utils import *
import sqlite3


def search(search_string):
    conn = sqlite3.connect('indexes')
    cur = conn.cursor()
    cur.execute('select path, name from indexes where field like ?', (f"%{search_string}%",))
    rows = cur.fetchall()
    cur.close()
    return rows


def lambda_handler(event, _):
    def create_body(_):
        query_params = event.get("queryStringParameters", {})
        search_term = query_params.get("q") if query_params else None
        rows = search(search_term)
        data = {row[0][:-5]: row[1] for row in rows}
        index_template = env.get_template("index.html")
        search_results = env.get_template("search_results.html")
        content = search_results.render(data=data)
        return index_template.render(content=content)

    return handler(event, create_body)
