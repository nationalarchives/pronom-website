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

pip install -r requirements.txt boto3 pycountry
mkdir -p site/fmt site/x-fmt site/actor site/edit/fmt site/edit/x-fmt site/actor/edit
python .github/scripts/generate_pages.py "$PWD/signature-files"
cd site || exit
aws s3 sync --quiet --content-type text/html . "s3://$ENVIRONMENT-pronom-website"
cd ..
python .github/scripts/generate_index_file.py "$PWD/signature-files"

mkdir -p package
pip install -r requirements.txt --target=package
cd package || exit
zip -q -r ../results.zip .
cd ../lambdas || exit
zip -q ../results.zip results.py
cd ..
zip -q ./results.zip ./lambdas/templates/index.html ./lambdas/templates/search_results.html  indexes

LATEST_SIGNATURE_FILE=$(aws s3 ls "s3://$ENVIRONMENT-pronom-website/signatures/" | sort -t'V' -k2,2n | tail -1 | awk '{split($0,a," "); print a[4]}')
aws lambda update-function-configuration --function-name pronom-soap --environment "Variables={DOWNLOAD_URL=https://d21gi86t6uhf68.cloudfront.net/signatures/$LATEST_SIGNATURE_FILE}" | cat > /dev/null

python .github/scripts/generate_version_file.py "$LATEST_SIGNATURE_FILE"
cd lambdas || exit
zip -q ../soap.zip soap.py version
cd ..

mkdir -p package-submissions
pip install ghapi --target=package-submissions
cd package-submissions || exit
zip -q -r ../submissions.zip .
cd ../lambdas || exit
zip -q ../submissions.zip submissions.py
cd ..

mkdir -p package-submissions-received
pip install -r requirements.txt --target=package-submissions-received
cd package-submissions-received || exit
zip -q -r ../submissions_received.zip .
cd ../lambdas || exit
zip -q ../submissions_received.zip submissions_received.py
cd ..
zip -q submissions_received.zip ./lambdas/templates/index.html ./lambdas/templates/submissions_received.html

cp ./*.zip infrastructure
cd infrastructure || exit
npm ci
npx cdk deploy --all -c environment="$ENVIRONMENT" --require-approval never