from flask import Flask, redirect, request

from lambdas.search import search

app = Flask(__name__)


@app.route("/healthcheck/live/")
def healthcheck():
    return "OK", 200


@app.route("/search")
def pronom_search():
    query_string = request.args.get("q")
    if query_string is not None:
        response = search.lambda_handler(
            {"queryStringParameters": {"q": query_string}}, None
        )
    else:
        response = search.lambda_handler({"queryStringParameters": {}}, None)
    if "body" in response:
        return response["body"]
    else:
        return redirect(response["headers"]["Location"], code=response["statusCode"])


if __name__ == "__main__":
    app.run()
