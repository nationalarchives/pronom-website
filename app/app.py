from flask import Flask, request, redirect
from lambdas.results import results
app = Flask(__name__)


@app.route("/results")
def search():
    query_string = request.args.get('q', '')
    response = results.lambda_handler({'queryStringParameters': {'q': query_string}}, None)
    if 'body' in response:
        return response['body']
    else:
        return redirect(response['headers']['Location'], code=response['statusCode'])
