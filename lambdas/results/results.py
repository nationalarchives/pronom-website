import math
import os
import re
import sqlite3

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


def puid_exists(puid):
    db_name = os.getenv("DB_NAME", "indexes")
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("SELECT path from indexes where path = ?", (puid,))
    rows = cursor.fetchall()
    return len(rows) > 0


def search(search_string):
    def sort_key(s: str):
        prefix, num = s[0].rsplit('/', 1)
        return prefix, int(num)

    db_name = os.getenv("DB_NAME", "indexes")
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()
    cur.execute(
        "select path, name from indexes where field like ?", (f"%{search_string}%",)
    )
    rows = cur.fetchall()
    cur.close()
    rows.sort(key=sort_key)
    return rows


def generate_pagination(current_page, start_page, total_pages, query):
    pages = []
    query_string = query if query else ""
    for i in range(start_page, total_pages + 1):
        page = {"number": i, "href": f"/results?q={query_string}&page={i}"}
        if i == current_page:
            page["current"] = True
        pages.append(page)
    return pages


def dedupe_pagination(pagination):
    seen = set()
    deduped = []

    for page in pagination:
        page_number = page.get("number")
        if not page_number:
            deduped.append(page)
        elif page_number not in seen:
            seen.add(page_number)
            deduped.append(page)
    return deduped


def get_pagination_data(rows, current_page, search_term):
    total_pages = math.ceil(len(rows) / 10)
    start_page = 1 if current_page == 1 or total_pages <= 3 else current_page - 1
    first_total_pages = current_page if current_page > 1 else current_page + 1
    first_page_items = generate_pagination(current_page, start_page, first_total_pages, search_term)
    second_page_items = generate_pagination(current_page, total_pages - 1, total_pages, search_term)
    ellipsis_entry = [] if total_pages - current_page <= 2 else [{"ellipsis": True}]
    page_one = {"href": f"/results?q={search_term}&page={1}", "number": 1}
    if current_page > 2:
        initial_items = [page_one]
        if current_page != 3:
            initial_items.append({"ellipsis": True})
    else:
        initial_items = []

    page_items = dedupe_pagination(initial_items + first_page_items + ellipsis_entry + second_page_items)

    previous_page = current_page - 1 if current_page > 1 else 1
    next_page = current_page + 1 if current_page <= total_pages else current_page
    return {
        "previous": {"href": f"/results?q={search_term}&page={previous_page}"},
        "next": {"href": f"/results?q={search_term}&page={next_page}"},
        "items": page_items
    }

def lambda_handler(event, _):
    query_params = event.get("queryStringParameters", {})
    search_term = query_params.get("q") if query_params else None
    if re.search(r"^(x-)?fmt\/\d{1,5}$", search_term) is not None and puid_exists(
        search_term
    ):
        return {"statusCode": 302, "headers": {"Location": search_term}}
    rows = search(search_term)
    current_page = int(query_params.get("page", '1'))
    pagination = get_pagination_data(rows, current_page, search_term) if len(rows) > 10 else {}

    start_idx = (current_page - 1) * 10
    end_idx = start_idx + min(len(rows), 10)
    filtered_rows = rows[start_idx:end_idx]
    data = {f"{row[0]}": row[1] for row in filtered_rows}
    search_results = env.get_template("search_results.html")
    body = search_results.render(data=data, search_term=search_term, pagination=pagination, total=len(rows), current_page=current_page)

    return {"statusCode": 200, "body": body, "headers": {"Content-Type": "text/html"}}
