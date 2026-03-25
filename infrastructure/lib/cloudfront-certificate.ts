import * as cdk from "aws-cdk-lib";
import {Construct} from "constructs";
import {HostedZone, IHostedZone} from "aws-cdk-lib/aws-route53";
import {Certificate, CertificateValidation} from "aws-cdk-lib/aws-certificatemanager";

class CertificateStack extends cdk.Stack {
    public readonly certificate: Certificate
    public readonly zone: IHostedZone

    constructor(scope: Construct, id: string, props?: cdk.StackProps) {
        super(scope, id, props)

        const zone = HostedZone.fromHostedZoneAttributes(this, "hostedZoneLookup", {
            zoneName: "pronom.nationalarchives.gov.uk",
            hostedZoneId: "Z0207922GVVLB5378323"
        })

        this.certificate = new Certificate(this, 'Certificate', {
            domainName: 'pronom.nationalarchives.gov.uk',
            validation: CertificateValidation.fromDnsMultiZone({
                'pronom.nationalarchives.gov.uk': zone
            }),
        })
        this.zone = zone
    }
}
export default CertificateStack