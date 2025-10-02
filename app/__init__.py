import os

from flask import Flask, redirect, request
from lambdas.results import results
from lambdas.submissions import submissions
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
            FileSystemLoader("/app/lambdas/templates"),
            PackageLoader("tna_frontend_jinja"),
        ]
    ),
    autoescape=select_autoescape(),
)

app = Flask(__name__)


@app.route("/healthcheck/live/")
def healthcheck():
    return "OK", 200


@app.route("/results")
def search():
    query_string = request.args.get("q", "")
    response = results.lambda_handler(
        {"queryStringParameters": {"q": query_string}}, None
    )
    if "body" in response:
        return response["body"]
    else:
        return redirect(response["headers"]["Location"], code=response["statusCode"])


@app.route("/submissions", methods=["POST"])
def create_pull_request():
    form_body = ""
    for k, v in request.form.items():
        form_body += f"{k}={v}&"

    response = submissions.lambda_handler(
        {"body": form_body}, None
    )
    if "body" in response:
        return response["body"]
    else:
        return redirect(response["headers"]["Location"], code=response["statusCode"])


@app.route("/submissions-received")
def submissions_received():
    print(os.getcwd())
    pr_number = request.args.get("number", "")

    submissions_received_template = env.get_template("submissions_received.html")
    body = submissions_received_template.render({"number": pr_number})

    return body


app.run()
