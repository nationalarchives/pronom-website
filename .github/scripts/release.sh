#!/bin/bash

set -e

ENVIRONMENT=$1

TNA_FRONTEND_VERSION=0.23.1
CDN_BASE_URL=https://cdn.jsdelivr.net/npm/@nationalarchives/frontend@$TNA_FRONTEND_VERSION/nationalarchives

curl $CDN_BASE_URL/all.css | aws s3 cp --content-type text/css - "s3://$ENVIRONMENT-pronom-website/all.css"
curl $CDN_BASE_URL/all.js | aws s3 cp --content-type text/javascript - "s3://$ENVIRONMENT-pronom-website/all.js"
curl $CDN_BASE_URL/font-awesome.css | sed -e 's/\/assets\/fonts/\//g' | aws s3 cp --content-type text/css - "s3://$ENVIRONMENT-pronom-website/font-awesome.css"
curl $CDN_BASE_URL/ie.css | aws s3 cp --content-type text/css - "s3://$ENVIRONMENT-pronom-website/ie.css"
curl $CDN_BASE_URL/print.css | aws s3 cp --content-type text/css - "s3://$ENVIRONMENT-pronom-website/print.css"
curl $CDN_BASE_URL/assets/images/favicon.ico | aws s3 cp --content-type image/x-icon - "s3://$ENVIRONMENT-pronom-website/favicon.ico"
curl $CDN_BASE_URL/assets/fonts/fa-solid-900.woff2 | aws s3 cp --content-type font/woff2 - "s3://$ENVIRONMENT-pronom-website/fa-solid-900.woff2"

python3 -m venv .venv
source .venv/bin/activate
pip install boto3 jinja2 tna-frontend-jinja
mkdir -p site/fmt site/x-fmt site/actor
python .github/scripts/generate_pages.py "$PWD/signature-files"
cd site || exit
aws s3 sync --quiet --content-type text/html . "s3://$ENVIRONMENT-pronom-website"
cd ..
python .github/scripts/generate_index_file.py "$PWD/signature-files"


cd lambdas/results
mkdir -p package
pip install --target=package .
cd package || exit
zip -q -r ../../../results.zip .
cd ../../../ || exit
zip -q ./results.zip ./lambdas/templates/index.html ./lambdas/templates/search_results.html  indexes

LATEST_SIGNATURE_FILE=$(aws s3 ls "s3://$ENVIRONMENT-pronom-website/signatures/" | sort -t'V' -k2,2n | tail -1 | awk '{split($0,a," "); print a[4]}')

python .github/scripts/generate_version_file.py "$LATEST_SIGNATURE_FILE"
cd lambdas || exit
cd soap
zip -rq ../../soap.zip .
cd ../../
zip -q soap.zip version

cp ./*.zip infrastructure
cd infrastructure || exit
npm ci
npx cdk deploy --all -c environment="$ENVIRONMENT" --require-approval never
aws lambda update-function-configuration --function-name $ENVIRONMENT-pronom-soap --environment "Variables={DOWNLOAD_URL=https://d21gi86t6uhf68.cloudfront.net/signatures/$LATEST_SIGNATURE_FILE}" | cat > /dev/null
