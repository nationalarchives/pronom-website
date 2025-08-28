#!/bin/bash

SIGNATURE_FILES_LOCATION=$1
mkdir -p site/fmt site/x-fmt site/actor site/edit/fmt site/edit/x-fmt site/actor/edit
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt pycountry ghapi boto3
python3 .github/scripts/generate_pages.py $SIGNATURE_FILES_LOCATION
python3 .github/scripts/generate_index_file.py $SIGNATURE_FILES_LOCATION
cd site
TNA_FRONTEND_VERSION=0.23.1
wget https://cdn.jsdelivr.net/npm/@nationalarchives/frontend@$TNA_FRONTEND_VERSION/nationalarchives/all.css -O all.css
wget https://cdn.jsdelivr.net/npm/@nationalarchives/frontend@$TNA_FRONTEND_VERSION/nationalarchives/all.js -O all.js
wget https://cdn.jsdelivr.net/npm/@nationalarchives/frontend@$TNA_FRONTEND_VERSION/nationalarchives/font-awesome.css -O font-awesome.css
wget https://cdn.jsdelivr.net/npm/@nationalarchives/frontend@$TNA_FRONTEND_VERSION/nationalarchives/ie.css -O ie.css
wget https://cdn.jsdelivr.net/npm/@nationalarchives/frontend@$TNA_FRONTEND_VERSION/nationalarchives/print.css -O print.css
wget https://cdn.jsdelivr.net/npm/@nationalarchives/frontend@$TNA_FRONTEND_VERSION/nationalarchives/assets/images/favicon.ico -O favicon.ico
wget https://cdn.jsdelivr.net/npm/@nationalarchives/frontend@$TNA_FRONTEND_VERSION/nationalarchives/assets/fonts/fa-solid-900.woff2 -O fa-solid-900.woff2
sed -i -e 's/\/assets\/fonts/\//g' font-awesome.css
cd ..
python3 http_server.py &
