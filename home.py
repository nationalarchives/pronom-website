from utils import *


def lambda_handler(event, _):
    def create_body(_):
        home_template = env.get_template("home.html")
        index_template = env.get_template("index.html")
        return index_template.render(content=home_template.render())

    return handler(event, create_body)


print(lambda_handler({}, None))