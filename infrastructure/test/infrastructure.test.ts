import * as cdk from "aws-cdk-lib";
import { Match, Template } from "aws-cdk-lib/assertions";
import * as inf from "../lib/infrastructure-stack";
import CertificateStack from "../lib/cloudfront-certificate";
import { InlineCode } from "aws-cdk-lib/aws-lambda";

jest.mock("aws-cdk-lib/aws-lambda", () => ({
  ...jest.requireActual("aws-cdk-lib/aws-lambda"),
  Code: {
    fromAsset: () => new InlineCode("echo"),
  },
}));

const app: cdk.App = new cdk.App();

let dnsStack = new CertificateStack(app, "test-dns-stack")
const stack: inf.InfrastructureStack = new inf.InfrastructureStack(
    app,
    "MyTestStack",
    dnsStack.zone,
    dnsStack.certificate,
);

const template: Template = Template.fromStack(stack);

test("All S3 buckets have SSE encryption and block public access", () => {
  template.allResourcesProperties("AWS::S3::Bucket", {
    BucketEncryption: {
      ServerSideEncryptionConfiguration: [
        { ServerSideEncryptionByDefault: { SSEAlgorithm: "AES256" } },
      ],
    },
    PublicAccessBlockConfiguration: {
      BlockPublicAcls: true,
      BlockPublicPolicy: true,
      IgnorePublicAcls: true,
      RestrictPublicBuckets: true,
    },
  });
});

test("All S3 bucket policies have a Deny on non-SSL requests", () => {
  template.hasResourceProperties('AWS::S3::BucketPolicy', Match.objectLike({
    PolicyDocument: {
      Statement: Match.arrayWith([Match.objectLike({
        Effect: "Deny",
        Principal: {
          AWS: "*",
        },
        Action: "s3:*",
        Resource: Match.anyValue(),
        Condition: {
          Bool: {
            "aws:SecureTransport": "false",
          },
        },
      })])
    }
  }));
});

test("Web ACLs should be attached to the REST APIs", () => {
  template.hasResourceProperties("AWS::WAFv2::WebACLAssociation", {
    ResourceArn: {
      "Fn::Join": [
        "",
        Match.arrayWith([
          "arn:",
          { Ref: "AWS::Partition" },
          ":apigateway:",
          { Ref: "AWS::Region" },
          "::/restapis/",
        ]),
      ],
    },
  });
});

test("Search lambda should allow Cloudfront OAC to access the function url", () => {
  template.hasResourceProperties('AWS::Lambda::Permission', Match.objectLike({
    Action: "lambda:InvokeFunctionUrl",
    FunctionName: Match.objectLike({
      'Fn::GetAtt': Match.arrayWith([
        Match.stringLikeRegexp('^searchresults'),
        Match.exact("FunctionArn"),
      ]),
    }),
    Principal: "cloudfront.amazonaws.com",
    SourceArn: Match.anyValue()
  }));
})

test("Cloudfront custom response headers policy has the correct values", () => {
  template.hasResourceProperties("AWS::CloudFront::ResponseHeadersPolicy", {
    ResponseHeadersPolicyConfig : {
      Comment : "Adds strict Content-Security-Policy for CloudFront responses",
      CustomHeadersConfig : {
        Items : [ {
          Header : "Permissions-Policy",
          Override : false,
          Value : "accelerometer=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), microphone=(), payment=(), usb=()"
        } ]
      },
      Name : "CspHeadersPolicy",
      SecurityHeadersConfig : {
        ContentSecurityPolicy : {
          ContentSecurityPolicy : "default-src 'self'; base-uri 'none'; object-src 'none'; font-src 'self' https://fonts.gstatic.com https://use.typekit.net; style-src 'self' https://www.nationalarchives.gov.uk https://fonts.googleapis.com https://p.typekit.net https://use.typekit.net; script-src 'self' https://www.nationalarchives.gov.uk",
          Override : true
        },
        ContentTypeOptions : {
          Override : false
        },
        FrameOptions : {
          FrameOption : "DENY",
          Override : false
        },
        ReferrerPolicy : {
          Override : false,
          ReferrerPolicy : "strict-origin"
        },
        StrictTransportSecurity : {
          AccessControlMaxAgeSec : 31536000,
          Override : false
        }
      }
    }
  })
})

test("All expected resources have been created", () => {
  template.resourceCountIs("AWS::ApiGateway::Account", 1);
  template.resourceCountIs("AWS::ApiGateway::Deployment", 1);
  template.resourceCountIs("AWS::ApiGateway::Method", 2);
  template.resourceCountIs("AWS::ApiGateway::Resource", 1);
  template.resourceCountIs("AWS::ApiGateway::RestApi", 1);
  template.resourceCountIs("AWS::ApiGateway::Stage", 1);
  template.resourceCountIs("AWS::CloudFront::Distribution", 1);
  template.resourceCountIs("AWS::CloudFront::OriginAccessControl", 3);
  template.resourceCountIs("AWS::CloudFront::ResponseHeadersPolicy", 2);
  template.resourceCountIs("AWS::IAM::Policy", 1);
  template.resourceCountIs("AWS::IAM::Role", 5);
  template.resourceCountIs("AWS::Lambda::Function", 3);
  template.resourceCountIs("AWS::Lambda::Permission", 6);
  template.resourceCountIs("AWS::Lambda::Url", 1);
  template.resourceCountIs("AWS::Route53::RecordSet", 2);
  template.resourceCountIs("AWS::S3::Bucket", 2);
  template.resourceCountIs("AWS::S3::BucketPolicy", 2);
  template.resourceCountIs("AWS::Scheduler::Schedule", 1);
  template.resourceCountIs("AWS::WAFv2::WebACL", 1);
  template.resourceCountIs("AWS::WAFv2::WebACLAssociation", 1);
  template.resourceCountIs("Custom::AWSCDKOpenIdConnectProvider", 1);
});
