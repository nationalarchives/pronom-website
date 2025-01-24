import * as cdk from 'aws-cdk-lib';
import {Match, Template} from 'aws-cdk-lib/assertions';
import * as cf from '../lib/cloudfront-waf'
import * as inf from '../lib/infrastructure-stack'
import {InlineCode} from "aws-cdk-lib/aws-lambda";

jest.mock("aws-cdk-lib/aws-lambda", () => ({
    ...jest.requireActual("aws-cdk-lib/aws-lambda"),
    Code: {
        fromAsset: () => new InlineCode("echo"),
    },
}))

const app: cdk.App = new cdk.App();
const infrastructureStack = new inf.InfrastructureStack(app, "TestInfrastructure")
const stack: cf.CloudFrontWAFStack = new cf.CloudFrontWAFStack(app, 'MyTestStack', infrastructureStack.cloudFrontDistribution);
const template: Template = Template.fromStack(stack);

test("All expected resources have been created", () => {
    template.resourceCountIs("AWS::WAFv2::WebACL", 1)
})
