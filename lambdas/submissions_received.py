from jinja2 import Environment, ChoiceLoader, PackageLoader, FileSystemLoader, select_autoescape

env = Environment(
    loader=ChoiceLoader([FileSystemLoader("lambdas/templates"), PackageLoader("tna_frontend_jinja"), ]),
    autoescape=select_autoescape()
)


def lambda_handler(event, context):
    pr_number = event['rawPath'].split('/')[-1]
    url = f'https://github.com/nationalarchives/pronom-signatures/pull/{pr_number}'
    index_template = env.get_template("index.html")
    submission_received_template = env.get_template('submissions_received.html')
    output_html = index_template.render(content=submission_received_template.render(pull_request_url=url))
    return {
        "headers": {"Content-Type": "text/html"},
        'statusCode': 200,
        'body': output_html
    }
