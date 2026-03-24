import * as cdk from "aws-cdk-lib";
import {Duration} from "aws-cdk-lib";
import {Construct} from "constructs";
import {CloudFrontToS3} from "@aws-solutions-constructs/aws-cloudfront-s3";
import {Bucket} from "aws-cdk-lib/aws-s3";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as origins from "aws-cdk-lib/aws-cloudfront-origins";
import * as cf from "aws-cdk-lib/aws-cloudfront";
import {
  AllowedMethods,
  HeadersFrameOption,
  HeadersReferrerPolicy,
  OriginRequestPolicy, ResponseCustomHeader,
  ResponseSecurityHeadersBehavior
} from "aws-cdk-lib/aws-cloudfront";
import * as agw from "aws-cdk-lib/aws-apigateway";
import {WafwebaclToApiGateway} from "@aws-solutions-constructs/aws-wafwebacl-apigateway";
import * as wafv2 from "aws-cdk-lib/aws-wafv2";
import { ServicePrincipal, OpenIdConnectProvider } from "aws-cdk-lib/aws-iam";
import { LambdaInvoke } from "aws-cdk-lib/aws-scheduler-targets";
import {Schedule, ScheduleExpression, ScheduleTargetInput} from "aws-cdk-lib/aws-scheduler";
import {AaaaRecord, IHostedZone, RecordTarget} from "aws-cdk-lib/aws-route53";
import {CloudFrontTarget} from "aws-cdk-lib/aws-route53-targets";
import { Certificate } from "aws-cdk-lib/aws-certificatemanager";

export class InfrastructureStack extends cdk.Stack {
  public readonly cloudFrontDistribution: cf.Distribution;
  public readonly rateLimitRule: wafv2.CfnWebACL.RuleProperty;

  constructor(scope: Construct, id: string, zone: IHostedZone, certificate: Certificate, props?: cdk.StackProps) {
    super(scope, id, props);
    const tryEnvironment = this.node.tryGetContext("environment");
    const environment: string = tryEnvironment
      ? (tryEnvironment as string)
      : "intg";

    const securityHeadersBehavior: ResponseSecurityHeadersBehavior = {
      contentSecurityPolicy: {
        contentSecurityPolicy:
          "default-src 'self'; base-uri 'none'; object-src 'none'; font-src 'self' https://fonts.gstatic.com https://use.typekit.net; style-src 'self' https://www.nationalarchives.gov.uk https://fonts.googleapis.com https://p.typekit.net https://use.typekit.net; script-src 'self' https://www.nationalarchives.gov.uk",
        override: true,
      },
      strictTransportSecurity: {
        accessControlMaxAge: Duration.days(365),
        override: false
      },
      contentTypeOptions: {
        override: false
      },
      frameOptions: {
        frameOption: HeadersFrameOption.DENY,
        override: false
      },
      referrerPolicy: {
        referrerPolicy: HeadersReferrerPolicy.STRICT_ORIGIN,
        override: false
      }
    };

    const permissionsPolicyHeader: ResponseCustomHeader = {
      header: 'Permissions-Policy',
      value: 'accelerometer=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), microphone=(), payment=(), usb=()',
      override: false
    }

    const responseHeadersPolicy = new cf.ResponseHeadersPolicy(
      this,
      "CspHeadersPolicy",
      {
        responseHeadersPolicyName: "CspHeadersPolicy",
        comment: "Adds strict Content-Security-Policy for CloudFront responses",
        securityHeadersBehavior,
        customHeadersBehavior: {
          customHeaders: [permissionsPolicyHeader]
        }
      },
    );

    const errorResponses = [403, 404, 500, 502, 503, 504].map(res => {
      return {
        httpStatus: res,
        responseHttpStatus: res,
        responsePagePath: "/error",
        ttl: cdk.Duration.minutes(0)
      }
    })

    const cloudfrontToS3: CloudFrontToS3 = new CloudFrontToS3(
      this,
      "pronom-website",
      {
        bucketProps: { versioned: false, bucketName: `${environment}-pronom-website`},
        logCloudFrontAccessLog: false,
        cloudFrontDistributionProps: { defaultRootObject: "home", errorResponses, enableLogging: false, domainNames: ["pronom.nationalarchives.gov.uk"], certificate },
        insertHttpSecurityHeaders: false,
        responseHeadersPolicyProps: {
          securityHeadersBehavior,
          customHeadersBehavior: {
            customHeaders: [permissionsPolicyHeader]
          }
        }
      },
    );

    new AaaaRecord(this, 'Alias', {
      zone,
      target: RecordTarget.fromAlias(new CloudFrontTarget(cloudfrontToS3.cloudFrontWebDistribution)),
    });

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

    const createLambda: (name: string, fileName: string) => lambda.Function = (
      name,
      fileName,
    ) => {
      return new lambda.Function(this, name, {
        functionName: `${environment}-pronom-${name}`,
        runtime: lambda.Runtime.PYTHON_3_13,
        handler: `${fileName}.lambda_handler`,
        code: lambda.Code.fromAsset(`${fileName}.zip`),
        timeout: Duration.minutes(1)
      });
    };

    const searchResults: lambda.Function = createLambda(
      "search-results",
      "results",
    );

    searchResults.addPermission("AllowCloudFrontInvokeFunction", {
      principal: new ServicePrincipal("cloudfront.amazonaws.com"),
      action: "lambda:InvokeFunction",
      sourceArn: cloudfrontToS3.cloudFrontWebDistribution.distributionArn,
    });

    const target = new LambdaInvoke(searchResults, {input: ScheduleTargetInput.fromObject({})})

    const schedule = ScheduleExpression.rate(Duration.minutes(5))

    new Schedule(this, "keep-warm-scheduler", {schedule, target})

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

    new OpenIdConnectProvider(this, "github-identity-provider", {url: "https://token.actions.githubusercontent.com", clientIds: ["sts.amazonaws.com"]})

    this.cloudFrontDistribution = cloudfrontToS3.cloudFrontWebDistribution;
  }
}
