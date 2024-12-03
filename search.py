from utils import *


def lambda_handler(event, _):
    def create_body(_):
        index_template = env.get_template("index.html")
        search_template = env.get_template("search.html")
        return index_template.render(content=search_template.render())

    return handler(event, create_body)
