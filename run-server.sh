#!/bin/bash

SIGNATURE_FILES_LOCATION=$1
mkdir -p site/fmt site/x-fmt site/actor site/edit/fmt site/edit/x-fmt site/actor/edit
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt pycountry ghapi boto3
python3 .github/scripts/generate_pages.py $SIGNATURE_FILES_LOCATION
python3 .github/scripts/generate_index_file.py $SIGNATURE_FILES_LOCATION
cd site
wget https://cdn.jsdelivr.net/npm/@nationalarchives/frontend@0.23.1/nationalarchives/all.css https://cdn.jsdelivr.net/npm/@nationalarchives/frontend@0.23.1/nationalarchives/all.js https://www.nationalarchives.gov.uk/favicon.ico
cd ..
python3 http_server.py
