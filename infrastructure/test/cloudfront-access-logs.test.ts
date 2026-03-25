import * as cdk from "aws-cdk-lib";
import {Match, Template} from "aws-cdk-lib/assertions";
import * as cal from "../lib/cloudfront-access-logs";
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
const stack: cal.default = new cal.default(
    app,
    "MyTestStack",
    infrastructureStack.cloudFrontDistribution,
);

const template: Template = Template.fromStack(stack);

test("The delivery destination is set", () => {
    template.hasResourceProperties('AWS::Logs::DeliveryDestination', Match.objectLike({
        Name: "distribution-logs-destination",
        OutputFormat: "json"
    }))
})

test("All expected resources have been created", () => {
    template.resourceCountIs("AWS::Logs::DeliverySource", 1);
    template.resourceCountIs("AWS::Logs::LogGroup", 1);
    template.resourceCountIs("AWS::Logs::DeliveryDestination", 1);
    template.resourceCountIs("AWS::Logs::Delivery", 1);
});

