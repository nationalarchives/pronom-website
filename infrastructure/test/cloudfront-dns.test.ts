import * as cdk from "aws-cdk-lib";
import {Match, Template} from "aws-cdk-lib/assertions";
import CertificateStack from "../lib/cloudfront-certificate";

const app: cdk.App = new cdk.App();
let stack = new CertificateStack(app, "test-dns-stack")

const template: Template = Template.fromStack(stack);

test("Certificate has the expected properties", () => {
    template.hasResourceProperties("AWS::CertificateManager::Certificate", {
        DomainName: "pronom.nationalarchives.gov.uk",
        DomainValidationOptions: [
            {
                DomainName: "pronom.nationalarchives.gov.uk",
                HostedZoneId: stack.zone.hostedZoneId
            }
        ],
        Tags: [
            {
                Key: "Name",
                Value: "test-dns-stack/Certificate"
            }
        ],
        ValidationMethod: "DNS"
    })
})

test("All expected resources have been created", () => {
    template.resourceCountIs("AWS::CertificateManager::Certificate", 1);
});