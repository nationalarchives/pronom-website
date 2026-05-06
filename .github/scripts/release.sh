#!/bin/bash

set -e

ENVIRONMENT=$1

S3_URL="s3://$ENVIRONMENT-pronom-site-$ACCOUNT_NUMBER-$REGION-an"

docker compose up -d --build
docker compose cp nginx:/usr/share/nginx/html/ .
docker compose exec app poetry run python .github/scripts/generate_index_file.py /home/app/pronom-signatures
docker compose cp app:/app/indexes .


cd html
aws s3 sync --content-type text/css  --exclude "*" --include "*.css" . $S3_URL
aws s3 sync --content-type text/javascript  --exclude "*" --include "*.js" . $S3_URL
aws s3 sync --content-type text/html  --exclude "*.css" --exclude "*.js" --exclude "fa-solid-900.woff2" . $S3_URL
aws s3 cp fa-solid-900.woff2 $S3_URL
cd ..

LATEST_SIGNATURE_FILE=$(aws s3 ls "$S3_URL/signatures/" | sort -t'V' -k2,2n | tail -1 | awk '{split($0,a," "); print a[4]}')
docker compose exec app poetry run python .github/scripts/generate_version_file.py "$LATEST_SIGNATURE_FILE"
docker compose cp app:/app/version .

cd lambdas/results
mkdir -p package
pip install --target=package .
cd package || exit
zip -q -r ../../../results.zip .
cd ../../../ || exit
zip -q ./results.zip ./lambdas/templates/index.html ./lambdas/templates/search_results.html  indexes

python .github/scripts/generate_version_file.py "$LATEST_SIGNATURE_FILE"
cd lambdas || exit
cd soap
zip -rq ../../soap.zip .
cd ../../
aws s3 cp "$S3_URL/signatures/$LATEST_SIGNATURE_FILE" signature-file.xml
zip -q soap.zip version signature-file.xml

cp ./*.zip terraform
cd terraform || exit
terraform init
TF_VAR_latest_signature_version=$LATEST_SIGNATURE_FILE terraform apply --auto-approve
aws cloudfront create-invalidation --distribution-id $(aws cloudfront list-distributions --query 'DistributionList.Items[0].Id' --output text) --paths "/*"
