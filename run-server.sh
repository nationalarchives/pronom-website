#!/bin/bash
set -e
SIGNATURE_FILES_LOCATION=$1
mkdir -p site/fmt site/x-fmt site/actor site/edit/fmt site/edit/x-fmt site/actor/edit
poetry install
python3 .github/scripts/generate_pages.py $SIGNATURE_FILES_LOCATION
python3 .github/scripts/generate_index_file.py $SIGNATURE_FILES_LOCATION
cd site
TNA_FRONTEND_VERSION=0.23.1
CDN_BASE_URL=https://cdn.jsdelivr.net/npm/@nationalarchives/frontend@$TNA_FRONTEND_VERSION/nationalarchives
wget $CDN_BASE_URL/all.css -O all.css
wget $CDN_BASE_URL/all.js -O all.js
wget $CDN_BASE_URL/font-awesome.css -O font-awesome.css
wget $CDN_BASE_URL/ie.css -O ie.css
wget $CDN_BASE_URL/print.css -O print.css
wget $CDN_BASE_URL/assets/images/favicon.ico -O favicon.ico
wget $CDN_BASE_URL/assets/fonts/fa-solid-900.woff2 -O fa-solid-900.woff2
sed -i -e 's/\/assets\/fonts/\//g' font-awesome.css
docker compose up -d --build
