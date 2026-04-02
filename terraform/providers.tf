terraform {
  backend "s3" {
    bucket       = "prod-pronom-site-terraform-state"
    key          = "terraform.state"
    region       = "eu-west-2"
    encrypt      = true
    use_lockfile = true
  }
}

provider "aws" {
  region = "eu-west-2"
}

provider "aws" {
  alias  = "use1"
  region = "us-east-1"
}
