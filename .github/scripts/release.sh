pip install boto3 pycountry requirements.txt
mkdir -p site/fmt site/x-fmt site/actor site/edit/fmt site/edit/x-fmt site/actor/edit
python .github/scripts/generate_pages.py "$PWD/signature-files"
cd site
aws s3 sync --quiet --content-type text/html . s3://tna-pronom-signatures-spike
cd ..
python .github/scripts/generate_index_file.py "$PWD/signature-files"

mkdir -p package
pip install -r requirements.txt --target=package
cd package
zip -q -r ../function.zip .
cd ../lambdas
zip -q ../function.zip ./templates/index.html ./templates/search_results.html results.py ../indexes
cd ..
aws lambda update-function-code --zip-file fileb://function.zip --function-name pronom-results | cat > /dev/null

LATEST_SIGNATURE_FILE=$(aws s3 ls s3://tna-pronom-signatures-spike/signatures/ | sort -t'V' -k2,2n | tail -1 | awk '{split($0,a," "); print a[4]}')
aws lambda update-function-configuration --function-name pronom-soap --environment Variables={DOWNLOAD_URL=https://d3hk4y84s0zka0.cloudfront.net/signatures/$LATEST_SIGNATURE_FILE}
while true; do
  status=$(aws lambda get-function --function-name pronom-soap --query 'Configuration.LastUpdateStatus' --output text)
  echo $status
  if [ "$status" = "Successful" ]; then
    echo "Update status is Successful. Proceeding..."
    break
  fi
  sleep 0.5
done
python .github/scripts/generate_version_file.py $LATEST_SIGNATURE_FILE
cd lambdas
zip -q ../function-soap.zip soap.py version
cd ..
aws lambda update-function-code --zip-file fileb://function-soap.zip --function-name pronom-soap | cat > /dev/null

mkdir -p package-submissions
pip install ghapi --target=package-submissions
cd package-submissions
zip -q -r ../submissions.zip .
cd ../lambdas
zip -q ../submissions.zip submissions.py
cd ..
aws lambda update-function-code --zip-file fileb://submissions.zip --function-name pronom-submissions | cat > /dev/null

mkdir -p package-submissions-received
pip install -r requirements.txt --target=package-submissions-received
cd package-submissions-received
zip -q -r ../submissions-received.zip .
cd ../lambdas
zip -q ../submissions-received.zip submissions_received.py ./templates/index.html ./templates/submissions_received.html
cd ..
aws lambda update-function-code --zip-file fileb://submissions-received.zip --function-name pronom-submission-received | cat > /dev/null