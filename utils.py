from jinja2 import Environment, ChoiceLoader, PackageLoader, FileSystemLoader, select_autoescape

env = Environment(
    loader=ChoiceLoader([FileSystemLoader("./templates"), PackageLoader("tna_frontend_jinja"), ]),
    autoescape=select_autoescape()
)

default_headers = {"Content-Type": "text/html"}


def handler(event, create_body, status_code=200, headers=None):
    if headers is None:
        headers = default_headers
    try:

        return {
            "statusCode": status_code,
            "body": create_body(event),
            "headers": headers
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": f"An error occurred: {str(e)}",
            "headers": {
                "Content-Type": "text/html"
            }
        }
