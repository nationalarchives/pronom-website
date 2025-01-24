import * as cdk from 'aws-cdk-lib';
import {Match, Template} from 'aws-cdk-lib/assertions';
import * as inf from '../lib/infrastructure-stack';
import {InlineCode} from "aws-cdk-lib/aws-lambda";


jest.mock("aws-cdk-lib/aws-lambda", () => ({
    ...jest.requireActual("aws-cdk-lib/aws-lambda"),
    Code: {
        fromAsset: () => new InlineCode("echo"),
    },
}))

const app: cdk.App = new cdk.App();
const stack: inf.InfrastructureStack = new inf.InfrastructureStack(app, 'MyTestStack');
const template: Template = Template.fromStack(stack);

test('All S3 buckets have SSE encryption and block public access', () => {
    template.allResourcesProperties("AWS::S3::Bucket", {
        "BucketEncryption": {"ServerSideEncryptionConfiguration":[{"ServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]},
        "PublicAccessBlockConfiguration": {
            "BlockPublicAcls": true,
            "BlockPublicPolicy": true,
            "IgnorePublicAcls": true,
            "RestrictPublicBuckets": true
        }
    })
});

test('All S3 bucket policies have a Deny on non-SSL requests', () => {
    template.hasResourceProperties("AWS::S3::BucketPolicy", Match.objectLike({
        PolicyDocument: {
            Version: "2012-10-17",
            Statement: [
                {
                    "Effect": "Deny",
                    "Principal": {
                        "AWS": "*"
                    },
                    "Action": "s3:*",
                    "Resource": Match.anyValue(),
                    "Condition": {
                        "Bool": {
                            "aws:SecureTransport": "false"
                        }
                    }
                },
            ]
        }
    }))
})

test("Web ACLs should be attached to the REST APIs", () => {
    template.hasResourceProperties("AWS::WAFv2::WebACLAssociation", {
        ResourceArn: {
            "Fn::Join" : ["", Match.arrayWith(["arn:",{"Ref": "AWS::Partition"},":apigateway:",{"Ref": "AWS::Region"},"::/restapis/"])]
        }
    })
})

test("All expected resources have been created", () => {
    template.resourceCountIs("AWS::Lambda::Function", 4)
    template.resourceCountIs("AWS::S3::Bucket", 4)
    template.resourceCountIs("AWS::ApiGateway::RestApi", 2)
    template.resourceCountIs("AWS::CloudFront::Distribution", 1)
    template.resourceCountIs("AWS::WAFv2::WebACL", 2)
})
