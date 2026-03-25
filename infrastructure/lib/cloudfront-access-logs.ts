import * as cf from "aws-cdk-lib/aws-cloudfront";
import * as cdk from "aws-cdk-lib";
import {Construct} from "constructs";
import {CfnDelivery, CfnDeliveryDestination, CfnDeliverySource, LogGroup} from "aws-cdk-lib/aws-logs";
import {Stack} from "aws-cdk-lib";

export class CloudfrontAccessLogsStack extends cdk.Stack {
    constructor(
        scope: Construct,
        id: string,
        cloudfrontDistribution: cf.Distribution,
        props?: cdk.StackProps,
    ) {
        super(scope, id, props);
        const distributionDeliverySource = new CfnDeliverySource(
            this,
            "DistributionDeliverySource",
            {
                name: "distribution-logs-source",
                logType: "ACCESS_LOGS",
                resourceArn: Stack.of(this).formatArn({
                    service: "cloudfront",
                    region: "",
                    resource: "distribution",
                    resourceName: cloudfrontDistribution.distributionId,
                }),
            },
        );

        const distributionDeliveryDestination = new CfnDeliveryDestination(
            this,
            "DistributionDeliveryDestination",
            {
                name: "distribution-logs-destination",
                destinationResourceArn: new LogGroup(this, "DistributionLogGroup")
                    .logGroupArn,
                outputFormat: "json",
            },
        );

        new CfnDelivery(this, "DistributionDelivery", {
                deliverySourceName: distributionDeliverySource.name,
                deliveryDestinationArn: distributionDeliveryDestination.attrArn,
            }
        ).node.addDependency(distributionDeliverySource);
    }


}
