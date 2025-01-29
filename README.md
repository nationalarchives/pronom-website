![Test](https://github.com/nationalarchives/pronom-website/actions/workflows/test.yml/badge.svg?branch=main)
![Release](https://github.com/nationalarchives/pronom-website/actions/workflows/release.yml/badge.svg)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

# PRONOM Website

This contains the code to generate the [PRONOM website](https://d21gi86t6uhf68.cloudfront.net/)

There are several components.

## GitHub Actions scripts
These are used to build various parts of the site.

### Generate index file
This takes a location on disk of the [signature files repository][signature_files_repository] as an argument. 
It parses all the json files in the `signatures/fmt` and `signatures/x-fmt` directories and adds the name, puid and file extension to a sqlite database. 
This is used to build the results lambda which processes search requests.

### Generate version file
This generates the XML for the latest version. This is returned by the soap lambda. 
This is only used to provide a legacy SOAP API and will be removed at a future date.

### Generate pages
This generates the static html for the site. The whole site is static html except for:
* The search results page
* The submission received page
These two have dynamic content that we don't know ahead of time.
The script uses jinja templates and data extracted from the [signature files repository][signature_files_repository] to generate the site.

## Lambda code
In the `lambdas/` directory, there are four lambda files.

### Results
This processes search results and renders the search results.

### Submissions
This processes each of the four possible submissions we can receive.
* Add an organisation
* Edit an organisation
* Add a file format
* Edit a file format
The lambda creates a pull request from a fork owned by the tna-pronom GitHub user with the relevant changes.

### Submissions Received
This renders a page with the GitHub pull request linked so users can follow the updates.

### SOAP
This replicates the behaviour of the legacy SOAP API

## Running locally
There is a script `run-server.sh` which will build and run a local copy of the site.

The script runs in the background with `nohup` To get it to run in the foreground, remove the call to nohup.

The dynamic routes in the local server are passed to the relevant lambda code except for the submissions' path. 
This returns a static submissions received page as I didn't want to create pull requests when testing it locally.

## Tests
There are two suites of tests

### Lambda tests
These are python unittest tests in the `lambdas/test` directory.
```bash
python -m unittest discover -s lambdas/test
```

### End-to-end tests
These are [Cypress](https://www.cypress.io/) tests which test the behaviour of a local copy of the site.
```bash
npm --prefix tests t
```

## Infrastructure
The AWS infrastructure is stored in the `infrastructure` directory and is written using [CDK](https://docs.aws.amazon.com/cdk/v2/guide/getting_started.html).

[signature_files_repository]: https://github.com/nationalarchives/pronom-signatures/