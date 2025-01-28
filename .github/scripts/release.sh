ENVIRONMENT=$1
curl https://cdn.jsdelivr.net/npm/@nationalarchives/frontend@0.2.15/nationalarchives/all.css | aws s3 cp --content-type text/css - s3://$ENVIRONMENT-pronom-website/all.css
curl https://cdn.jsdelivr.net/npm/@nationalarchives/frontend@0.2.15/nationalarchives/all.js | aws s3 cp --content-type text/javascript - s3://$ENVIRONMENT-pronom-website/all.js
curl https://www.nationalarchives.gov.uk/favicon.ico | aws s3 cp --content-type image/x-icon - s3://$ENVIRONMENT-pronom-website/favicon.ico

pip install -r requirements.txt boto3 pycountry
mkdir -p site/fmt site/x-fmt site/actor site/edit/fmt site/edit/x-fmt site/actor/edit
python .github/scripts/generate_pages.py "$PWD/signature-files"
cd site
aws s3 sync --quiet --content-type text/html . s3://$ENVIRONMENT-pronom-website
cd ..
python .github/scripts/generate_index_file.py "$PWD/signature-files"

mkdir -p package
pip install -r requirements.txt --target=package
cd package
zip -q -r ../results.zip .
cd ../lambdas
zip -q ../results.zip results.py
cd ..
zip -q ./results.zip ./lambdas/templates/index.html ./lambdas/templates/search_results.html  indexes

LATEST_SIGNATURE_FILE=$(aws s3 ls s3://$ENVIRONMENT-pronom-website/signatures/ | sort -t'V' -k2,2n | tail -1 | awk '{split($0,a," "); print a[4]}')
aws lambda update-function-configuration --function-name pronom-soap --environment Variables={DOWNLOAD_URL=https://d3hk4y84s0zka0.cloudfront.net/signatures/$LATEST_SIGNATURE_FILE} | cat > /dev/null

python .github/scripts/generate_version_file.py $LATEST_SIGNATURE_FILE
cd lambdas
zip -q ../soap.zip soap.py version
cd ..

mkdir -p package-submissions
pip install ghapi --target=package-submissions
cd package-submissions
zip -q -r ../submissions.zip .
cd ../lambdas
zip -q ../submissions.zip submissions.py
cd ..

mkdir -p package-submissions-received
pip install -r requirements.txt --target=package-submissions-received
cd package-submissions-received
zip -q -r ../submissions_received.zip .
cd ../lambdas
zip -q ../submissions_received.zip submissions_received.py
cd ..
zip -q submissions_received.zip ./lambdas/templates/index.html ./lambdas/templates/submissions_received.html

cp *.zip infrastructure
cd infrastructure
npm ci
npx cdk deploy --all -c environment=$ENVIRONMENT --require-approval never