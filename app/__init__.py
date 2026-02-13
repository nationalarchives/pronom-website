from flask import Flask, redirect, request
from lambdas.results import results

app = Flask(__name__)


@app.route("/healthcheck/live/")
def healthcheck():
    return "OK", 200


@app.route("/results")
def search():
    query_string = request.args.get("q", "")
    page = request.args.get("page", "")
    response = results.lambda_handler(
        {"queryStringParameters": {"q": query_string, "page": page}}, None
    )
    if "body" in response:
        return response["body"]
    else:
        return redirect(response["headers"]["Location"], code=response["statusCode"])
