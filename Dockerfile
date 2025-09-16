FROM ghcr.io/nationalarchives/tna-python-dev
ARG SIGNATURE_FILES_LOCATION="../pronom-signatures"
COPY pyproject.toml poetry.lock ./
RUN tna-build
RUN mkdir -p site/fmt site/x-fmt site/actor site/edit/fmt site/edit/x-fmt site/actor/edit; \
    . tna-nvm && npm install @nationalarchives/frontend@0.25.1; \
    cp node_modules/@nationalarchives/frontend/nationalarchives/all.css site/all.css; \
    cp node_modules/@nationalarchives/frontend/nationalarchives/all.js site/all.js; \
    cp node_modules/@nationalarchives/frontend/nationalarchives/font-awesome.css site/font-awesome.css; \
    cp node_modules/@nationalarchives/frontend/nationalarchives/ie.css site/ie.css; \
    cp node_modules/@nationalarchives/frontend/nationalarchives/print.css site/print.css; \
    cp node_modules/@nationalarchives/frontend/nationalarchives/assets/images/favicon.ico site/favicon.ico; \
    cp node_modules/@nationalarchives/frontend/nationalarchives/assets/fonts/fa-solid-900.woff2 site/fa-solid-900.woff2; \
    sed -i -e 's/\/assets\/fonts/\//g' site/font-awesome.css
RUN git clone https://github.com/nationalarchives/pronom-signatures/ /home/app/pronom-signatures
COPY . .
RUN poetry run python .github/scripts/generate_pages.py /home/app/pronom-signatures; \
    poetry run python .github/scripts/generate_index_file.py /home/app/pronom-signatures
CMD ["tna-run", "app:app"]
