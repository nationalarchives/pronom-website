variable "environment" {
  type    = string
  default = "prod"
}

variable "hosted_zone_id" {
  description = "Route53 hosted zone id for pronom.nationalarchives.gov.uk."
  type        = string
  default     = "Z0207922GVVLB5378323"
}

variable "latest_signature_version" {}