#!/usr/bin/env node
import * as cdk from "aws-cdk-lib";
import { InfrastructureStack } from "../lib/infrastructure-stack";
import { CloudFrontWAFStack } from "../lib/cloudfront-waf";

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

const infrastructure = new InfrastructureStack(
  app,
  "pronom-website",
  londonProps,
);

new CloudFrontWAFStack(
  app,
  "cloudfront-waf",
  infrastructure.cloudFrontDistribution,
  infrastructure.rateLimitRule,
  virginiaProps,
);
