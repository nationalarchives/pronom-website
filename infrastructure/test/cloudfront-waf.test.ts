import * as cdk from "aws-cdk-lib";
import { Template } from "aws-cdk-lib/assertions";
import * as cf from "../lib/cloudfront-waf";
import * as inf from "../lib/infrastructure-stack";
import { InlineCode } from "aws-cdk-lib/aws-lambda";
import CertificateStack from "../lib/cloudfront-certificate";

jest.mock("aws-cdk-lib/aws-lambda", () => ({
  ...jest.requireActual("aws-cdk-lib/aws-lambda"),
  Code: {
    fromAsset: () => new InlineCode("echo"),
  },
}));

const app: cdk.App = new cdk.App();
let dnsStack = new CertificateStack(app, "test-dns-stack")
const infrastructureStack = new inf.InfrastructureStack(
  app,
  "TestInfrastructure",
    dnsStack.zone,
    dnsStack.certificate,
);
const stack: cf.default = new cf.default(
  app,
  "MyTestStack",
  infrastructureStack.cloudFrontDistribution,
  infrastructureStack.rateLimitRule,
);
const template: Template = Template.fromStack(stack);

test("WAF rules are set correctly", () => {
  template.hasResourceProperties("AWS::WAFv2::WebACL", {
    "DefaultAction" : {
      "Allow" : { }
    },
    "Rules" : [ {
      "Action" : {
        "Block" : { }
      },
      "Name" : "RateLimit15000",
      "Priority" : 1,
      "Statement" : {
        "RateBasedStatement" : {
          "AggregateKeyType" : "IP",
          "Limit" : 15000
        }
      },
      "VisibilityConfig" : {
        "CloudWatchMetricsEnabled" : true,
        "MetricName" : "RateLimit15000",
        "SampledRequestsEnabled" : true
      }
    } ],
    "Scope" : "CLOUDFRONT",
    "VisibilityConfig" : {
      "CloudWatchMetricsEnabled" : true,
      "MetricName" : "webACL",
      "SampledRequestsEnabled" : true
    }
  })
})

test("All expected resources have been created", () => {
  template.resourceCountIs("AWS::WAFv2::WebACL", 1);
});
