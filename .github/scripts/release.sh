#!/bin/bash

set -e

ENVIRONMENT=$1


S3_BUCKET="$ENVIRONMENT-pronom-site-$ACCOUNT_NUMBER-$REGION-an"
S3_URL="s3://$S3_BUCKET"

docker compose up -d --build
docker compose cp nginx:/usr/share/nginx/html/ .
docker compose exec app poetry run python .github/scripts/generate_index_file.py /home/app/pronom-signatures
docker compose cp app:/home/app/indexes .

LATEST_SIGNATURE_FILE=DROID_SignatureFile_$(gh api repos/nationalarchives/pronom/releases/latest | jq -r '.name').xml
docker compose exec app poetry run python .github/scripts/generate_version_file.py "$LATEST_SIGNATURE_FILE"
docker compose cp app:/app/version .

cd lambdas/results
mkdir -p package
pip install --target=package .
cd package || exit
zip -q -r ../../../results.zip .
cd ../../../ || exit
zip -q ./results.zip ./lambdas/templates/index.html ./lambdas/templates/search_results.html indexes

python .github/scripts/generate_version_file.py "$LATEST_SIGNATURE_FILE"
cd lambdas || exit
cd soap
zip -rq ../../soap.zip .
cd ../../
wget $(gh api repos/nationalarchives/pronom/releases/latest | jq -r '.assets[] | select(.name | startswith("DROID")) | .browser_download_url')
mv $LATEST_SIGNATURE_FILE signature-file.xml
zip -q soap.zip version signature-file.xml

cp ./*.zip terraform
cd terraform || exit
terraform init
terraform workspace select $ENVIRONMENT
TF_VAR_environment=$ENVIRONMENT TF_VAR_latest_signature_version=$LATEST_SIGNATURE_FILE terraform apply --auto-approve
cd ..

python .github/scripts/upload_signature_files.py $S3_BUCKET

cd html
aws s3 sync --content-type text/css  --exclude "*" --include "*.css" . $S3_URL
aws s3 sync --content-type text/javascript  --exclude "*" --include "*.js" . $S3_URL
aws s3 sync --content-type text/html  --exclude "*.css" --exclude "*.js" --exclude "fa-solid-900.woff2" . $S3_URL
aws s3 cp fa-solid-900.woff2 $S3_URL
aws s3 cp signatures.json $S3_URL

aws cloudfront create-invalidation --distribution-id $(aws cloudfront list-distributions --query 'DistributionList.Items[0].Id' --output text) --paths "/*"
