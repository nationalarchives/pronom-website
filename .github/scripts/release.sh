#!/bin/bash

set -e

ENVIRONMENT=$1

S3_URL="s3://$ENVIRONMENT-pronom-website"

docker compose up -d --build
docker compose cp nginx:/usr/share/nginx/html/ .
docker compose exec app poetry run python .github/scripts/generate_index_file.py /home/app/pronom-signatures
docker compose cp p:/app/indexes .


cd html
aws s3 sync --content-type text/css  --exclude "*" --include "*.css" . $S3_URL
aws s3 sync --content-type text/javascript  --exclude "*" --include "*.js" . $S3_URL
aws s3 sync --content-type text/html  --exclude "*.css" --exclude "*.js" --exclude "fa-solid-900.woff2" . $S3_URL
aws s3 cp fa-solid-900.woff2 $S3_URL
cd ..

LATEST_SIGNATURE_FILE=$(aws s3 ls "s3://$ENVIRONMENT-pronom-website/signatures/" | sort -t'V' -k2,2n | tail -1 | awk '{split($0,a," "); print a[4]}')
docker compose exec app poetry run python .github/scripts/generate_version_file.py "$LATEST_SIGNATURE_FILE"
docker compose cp p:/app/version .

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
zip -q soap.zip version

cp ./*.zip infrastructure
cd infrastructure || exit
npm ci
npx cdk deploy --all -c environment="$ENVIRONMENT" --require-approval never
aws lambda update-function-configuration --function-name $ENVIRONMENT-pronom-soap --environment "Variables={DOWNLOAD_URL=https://d21gi86t6uhf68.cloudfront.net/signatures/$LATEST_SIGNATURE_FILE}" | cat > /dev/null
