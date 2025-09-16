import * as cdk from "aws-cdk-lib";
import { Construct } from "constructs";
import { CloudFrontToS3 } from "@aws-solutions-constructs/aws-cloudfront-s3";
import { Bucket, BucketProps } from "aws-cdk-lib/aws-s3";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as origins from "aws-cdk-lib/aws-cloudfront-origins";
import * as cf from "aws-cdk-lib/aws-cloudfront";
import {
  AllowedMethods,
  OriginRequestPolicy,
} from "aws-cdk-lib/aws-cloudfront";
import * as agw from "aws-cdk-lib/aws-apigateway";
import { WafwebaclToApiGateway } from "@aws-solutions-constructs/aws-wafwebacl-apigateway";
import { Effect, PolicyStatement } from "aws-cdk-lib/aws-iam";
import { StringParameter } from "aws-cdk-lib/aws-ssm";
import * as wafv2 from "aws-cdk-lib/aws-wafv2";

export class InfrastructureStack extends cdk.Stack {
  public readonly cloudFrontDistribution: cf.Distribution;
  public readonly rateLimitRule: wafv2.CfnWebACL.RuleProperty;

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);
    const tryEnvironment = this.node.tryGetContext("environment");
    const environment: string = tryEnvironment
      ? (tryEnvironment as string)
      : "intg";
    const bucketProps: (suffix: string) => BucketProps = (suffix) => {
      return { bucketName: `${environment}-pronom-website${suffix}` };
    };

    const securityHeadersBehavior = {
      contentSecurityPolicy: {
        contentSecurityPolicy:
          "default-src 'self'; base-uri 'none'; object-src 'none'; font-src 'self' https://fonts.gstatic.com https://use.typekit.net; style-src 'self' https://www.nationalarchives.gov.uk https://fonts.googleapis.com https://p.typekit.net https://use.typekit.net; script-src 'self' https://www.nationalarchives.gov.uk",
        override: true,
      },
    };

    const responseHeadersPolicy = new cf.ResponseHeadersPolicy(
      this,
      "CspHeadersPolicy",
      {
        responseHeadersPolicyName: "CspHeadersPolicy",
        comment: "Adds strict Content-Security-Policy for CloudFront responses",
        securityHeadersBehavior,
      },
    );

    const cloudfrontToS3: CloudFrontToS3 = new CloudFrontToS3(
      this,
      "pronom-website",
      {
        bucketProps: { versioned: false, ...bucketProps("") },
        loggingBucketProps: bucketProps("-logs"),
        cloudFrontLoggingBucketProps: bucketProps("-cloudfront-logs"),
        cloudFrontLoggingBucketAccessLogBucketProps: bucketProps(
          "-cloudfront-logs-access-logs",
        ),
        cloudFrontDistributionProps: { defaultRootObject: "home" },
        insertHttpSecurityHeaders: false,
        responseHeadersPolicyProps: { securityHeadersBehavior },
      },
    );

    const rateLimitRule: wafv2.CfnWebACL.RuleProperty = {
      name: "RateLimit15000",
      priority: 1,
      action: {
        block: {},
      },
      statement: {
        rateBasedStatement: {
          limit: 15000,
          aggregateKeyType: "IP",
        },
      },
      visibilityConfig: {
        sampledRequestsEnabled: true,
        cloudWatchMetricsEnabled: true,
        metricName: "RateLimit15000",
      },
    };

    this.rateLimitRule = rateLimitRule;

    const parameterArn: string =
      StringParameter.fromSecureStringParameterAttributes(
        this,
        "github-token",
        {
          parameterName: "/github/token",
        },
      ).parameterArn;

    const createLambda: (name: string, fileName: string) => lambda.Function = (
      name,
      fileName,
    ) => {
      return new lambda.Function(this, name, {
        functionName: `${environment}-pronom-${name}`,
        runtime: lambda.Runtime.PYTHON_3_13,
        handler: `${fileName}.lambda_handler`,
        code: lambda.Code.fromAsset(`${fileName}.zip`),
      });
    };

    const searchResults: lambda.Function = createLambda(
      "search-results",
      "results",
    );

    const soap: lambda.Function = createLambda("soap", "soap");

    const searchResultsUrl: lambda.FunctionUrl = searchResults.addFunctionUrl({
      authType: lambda.FunctionUrlAuthType.AWS_IAM,
    });

    const soapRESTAPI: agw.RestApi = new agw.LambdaRestApi(this, "soapApi", {
      handler: soap,
      defaultMethodOptions: { authorizer: undefined },
    });

    cloudfrontToS3.cloudFrontWebDistribution.addBehavior(
      "/results",
      origins.FunctionUrlOrigin.withOriginAccessControl(searchResultsUrl),
      {
        cachePolicy: cf.CachePolicy.CACHING_DISABLED,
        originRequestPolicy: OriginRequestPolicy.ALL_VIEWER_EXCEPT_HOST_HEADER,
        responseHeadersPolicy,
      },
    );

    const bucket: Bucket | undefined = cloudfrontToS3.s3Bucket;
    if (bucket != undefined) {
      cloudfrontToS3.cloudFrontWebDistribution.addBehavior(
        "/signature*",
        origins.S3BucketOrigin.withOriginAccessControl(bucket),
        {
          cachePolicy: cf.CachePolicy.CACHING_DISABLED,
        },
      );
    }

    cloudfrontToS3.cloudFrontWebDistribution.addBehavior(
      "/service.asmx",
      new origins.RestApiOrigin(soapRESTAPI, {}),
      {
        cachePolicy: cf.CachePolicy.CACHING_DISABLED,
        originRequestPolicy: OriginRequestPolicy.ALL_VIEWER_EXCEPT_HOST_HEADER,
        allowedMethods: AllowedMethods.ALLOW_ALL,
      },
    );

    new WafwebaclToApiGateway(this, "pronom-soap-wafwebacl-apigateway", {
      existingApiGatewayInterface: soapRESTAPI,
      webaclProps: {
        rules: [rateLimitRule],
      },
    });

    this.cloudFrontDistribution = cloudfrontToS3.cloudFrontWebDistribution;
  }
}
