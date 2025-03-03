import * as waclcf from "@aws-solutions-constructs/aws-wafwebacl-cloudfront";
import * as cf from "aws-cdk-lib/aws-cloudfront";
import * as cdk from 'aws-cdk-lib';
import {Construct} from "constructs";

export class CloudFrontWAFStack extends cdk.Stack {
    constructor(scope: Construct, id: string, cloudfrontDistribution: cf.Distribution, props?: cdk.StackProps) {
        super(scope, id, props);
        const tryEnvironment = this.node.tryGetContext("environment")
        const environment: string = tryEnvironment ? tryEnvironment as string : "intg"

        new waclcf.WafwebaclToCloudFront(this, `${environment}-wafwebacl-pronom-website`, {
            existingCloudFrontWebDistribution: cloudfrontDistribution
        });
    }
}
