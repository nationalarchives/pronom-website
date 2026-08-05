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

cd lambdas/search
mkdir -p package
pip install --target=package .
cd package || exit
zip -q -r ../../../search.zip .
cd ../../../ || exit
zip -q ./search.zip ./lambdas/templates/index.html ./lambdas/templates/search_results.html ./lambdas/templates/_base.html indexes

python .github/scripts/generate_version_file.py "$LATEST_SIGNATURE_FILE"
cd lambdas || exit
cd soap
zip -rq ../../soap.zip .
cd ../../
wget $(gh api repos/nationalarchives/pronom/releases/latest | jq -r '.assets[] | select(.name | startswith("DROID")) | .browser_download_url') -O signature-file.xml
wget $(gh api repos/nationalarchives/pronom/releases/latest | jq -r '.assets[] | select(.name | startswith("container")) | .browser_download_url') -O container-signatures.xml
zip -q soap.zip version signature-file.xml

cp ./*.zip terraform
cd terraform || exit
terraform init
terraform workspace select $ENVIRONMENT
TF_VAR_environment=$ENVIRONMENT TF_VAR_latest_signature_version=$LATEST_SIGNATURE_FILE terraform apply --auto-approve
cd ..

python .github/scripts/upload_signature_files.py $S3_BUCKET

cd html
aws s3 sync --content-type text/css --cache-control max-age=2592000 --exclude "*" --include "*.css" . $S3_URL
aws s3 sync --content-type text/javascript --cache-control max-age=2592000 --exclude "*" --include "*.js" . $S3_URL
aws s3 sync --content-type application/xml --cache-control max-age=2592000 --exclude "*" --include "*.xml" . $S3_URL
aws s3 sync --content-type image/x-icon --cache-control max-age=31536000 --exclude "*" --include "*.ico" . $S3_URL
aws s3 sync --content-type image/png --cache-control max-age=31536000 --exclude "*" --include "*.png" . $S3_URL
aws s3 sync --content-type image/webp --cache-control max-age=31536000 --exclude "*" --include "*.webp" . $S3_URL
aws s3 sync --content-type application/json --cache-control max-age=2592000 --exclude "*" --include "*.json" . $S3_URL
aws s3 cp --content-type font/woff2 --cache-control max-age=31536000 assets/fa-solid-900.woff2 $S3_URL/assets//fa-solid-900.woff2
aws s3 cp --content-type font/woff2 --cache-control max-age=31536000 assets/fa-brands-400.woff2 $S3_URL/assets//fa-brands-400.woff2
aws s3 sync --content-type text/html --cache-control max-age=2592000 --exclude "*.css" --exclude "*.js" --exclude "*.xml" --exclude "*.woff2" --exclude "*.ico" --exclude "*.png" --exclude "*.webp" --exclude "*.json" . $S3_URL
aws s3 cp signatures.json $S3_URL
aws s3 mv $S3_URL/releases.html $S3_URL/releases
aws s3 cp ../signature-file.xml $S3_URL/binary-signatures.xml
aws s3 cp ../container-signatures.xml $S3_URL/container-signatures.xml

aws cloudfront create-invalidation --distribution-id $(aws cloudfront list-distributions --query 'DistributionList.Items[0].Id' --output text) --paths "/*"
