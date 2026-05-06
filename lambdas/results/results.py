import os
import re
import sqlite3
from contextlib import closing

from jinja2 import (
    ChoiceLoader,
    Environment,
    FileSystemLoader,
    PackageLoader,
    select_autoescape,
)

env = Environment(
    loader=ChoiceLoader(
        [
            FileSystemLoader("./lambdas/templates"),
            PackageLoader("tna_frontend_jinja"),
        ]
    ),
    autoescape=select_autoescape(),
)

env.filters["commafy"] = lambda x: f"{x:,d}"


def puid_exists(puid):
    db_name = os.getenv("DB_NAME", "indexes")
    with closing(sqlite3.connect(db_name)) as conn:
        with closing(conn.cursor()) as cur:
            cur.execute("SELECT path from formats where path = ?", (puid,))
            rows = cur.fetchall()
    return len(rows) > 0


def search(search_string):
    def sort_key(s: str):
        prefix, num = s[0].rsplit("/", 1)
        return prefix, int(num)

    db_name = os.getenv("DB_NAME", "indexes")
    with closing(sqlite3.connect(db_name)) as conn:
        with closing(conn.cursor()) as cur:
            base_query = "select path, f.name, group_concat(e.name, ', ') from formats f join extensions e on e.format_id = f.id"
            group_by = "group by path, f.name"
            if search_string.startswith(".") and len(search_string) > 1:
                cur.execute(
                    f"{base_query} where id in (select format_id from extensions where name = ?) {group_by}",
                    (search_string[1:],),
                )
            elif search_string.strip() == ".":
                return []
            else:
                cur.execute(
                    f"{base_query} where field like ? {group_by}",
                    (f"%{search_string}%",),
                )
            rows = cur.fetchall()
            rows.sort(key=sort_key)
    return rows


def lambda_handler(event, _):
    query_params = event.get("queryStringParameters", {})
    if query_params:
        search_term = query_params.get("q") if query_params else None
        if re.search(
            r"^(x-)?fmt\/\d{1,5}$", search_term.lower()
        ) is not None and puid_exists(search_term.lower()):
            return {"statusCode": 302, "headers": {"Location": search_term.lower()}}
        rows = search(search_term)
        data = [{"puid": row[0], "name": row[1], "extensions": row[2]} for row in rows]
        search_results = env.get_template("search_results.html")
        body = search_results.render(data=data, search_term=search_term)

        return {
            "statusCode": 200,
            "body": body,
            "headers": {"Content-Type": "text/html"},
        }
    return {"statusCode": 200}
