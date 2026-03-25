#!/usr/bin/env node
import * as cdk from "aws-cdk-lib";
import { InfrastructureStack } from "../lib/infrastructure-stack";
import CloudFrontWAFStack from "../lib/cloudfront-waf";
import { CloudfrontAccessLogsStack } from "../lib/cloudfront-access-logs";
import {DNSStack} from "../lib/cloudfront-dns";

const londonProps: cdk.StackProps = {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION,
  },
  crossRegionReferences: true,
};
const virginiaProps: cdk.StackProps = {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: "us-east-1",
  },
  crossRegionReferences: true,
};
const app: cdk.App = new cdk.App();

const dns = new DNSStack(app, "website-dns", virginiaProps)

const infrastructure = new InfrastructureStack(
  app,
  "pronom-website",
  dns.zone,
  dns.certificate,
  londonProps,
);

new CloudFrontWAFStack(
  app,
  "cloudfront-waf",
  infrastructure.cloudFrontDistribution,
  infrastructure.rateLimitRule,
  virginiaProps,
);

new CloudfrontAccessLogsStack(
    app,
    "cloudfront-access-logs",
    infrastructure.cloudFrontDistribution,
    virginiaProps
)