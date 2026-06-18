resource "aws_iam_openid_connect_provider" "github" {
  count = var.environment == "prod" ? 1 : 0
  url            = "https://token.actions.githubusercontent.com"
  client_id_list = ["sts.amazonaws.com"]
}