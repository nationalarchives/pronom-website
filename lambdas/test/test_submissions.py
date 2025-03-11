import unittest
from unittest.mock import patch
from base64 import b64encode, b64decode
from lambdas import submissions
from fastcore.net import HTTPError
import io
import zipfile
import json


class SubmissionsTest(unittest.TestCase):

    @staticmethod
    def create_zip_file(signature, actor):
        in_memory_zip = io.BytesIO()
        with zipfile.ZipFile(in_memory_zip, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("repo/signatures/fmt/1.json", json.dumps(signature))
            zf.writestr("repo/actors/1.json", json.dumps(actor))
        in_memory_zip.seek(0)
        return in_memory_zip.getvalue()

    def assert_pr_not_created(self, mock_gh_api, form_body, signature, actor):
        mock_instance = mock_gh_api.return_value
        mock_instance.repos.download_zipball_archive.return_value = self.create_zip_file(signature, actor)
        submissions.lambda_handler({'body': form_body}, None)
        self.assertEqual(mock_instance.repos.create_or_update_file_contents.call_count, 0)

    def run_lambda(self, mock_gh_api, form_body, signature, actor):
        mock_instance = mock_gh_api.return_value
        mock_instance.repos.download_zipball_archive.return_value = self.create_zip_file(signature, actor)
        submissions.lambda_handler({'body': form_body}, None)
        return mock_instance

    def get_pr_file_contents(self, mock_gh_api, form_body, signature, actor):
        mock_instance = self.run_lambda(mock_gh_api, form_body, signature, actor)
        create_pr_arguments = mock_instance.repos.create_or_update_file_contents.mock_calls[0].kwargs
        return json.loads(b64decode(create_pr_arguments['content']))

    @patch('lambdas.submissions.GhApi')
    @patch('boto3.client')
    def test_edit_format_missing_field(self, _, mock_gh_api):
        form_body = 'submissionType=edit-format&puid=fmt/1&formatName=testName'
        pr_file_content = self.get_pr_file_contents(mock_gh_api, form_body, {}, {})
        self.assertEqual(pr_file_content['formatName'], 'testName')

    @patch('lambdas.submissions.GhApi')
    @patch('boto3.client')
    def test_edit_format_existing_field(self, _, mock_gh_api):
        form_body = 'submissionType=edit-format&puid=fmt/1&formatName=testName'
        signature = {'formatName': 'originalName'}
        pr_file_content = self.get_pr_file_contents(mock_gh_api, form_body, signature, {})
        self.assertEqual(pr_file_content['formatName'], 'testName')

    @patch('lambdas.submissions.GhApi')
    @patch('boto3.client')
    def test_edit_add_to_missing_identifiers(self, _, mock_gh_api):
        form_body = 'submissionType=edit-format&puid=fmt/1&identifierType=testIdentifier&identifierText=testValue'
        pr_file_content = self.get_pr_file_contents(mock_gh_api, form_body, {}, {})
        identifiers = pr_file_content['identifiers']
        self.assertEqual(len(identifiers), 1)
        self.assertEqual(identifiers[0]['identifierText'], 'testValue')
        self.assertEqual(identifiers[0]['identifierType'], 'testIdentifier')

    @patch('lambdas.submissions.GhApi')
    @patch('boto3.client')
    def test_edit_add_to_existing_identifiers(self, _, mock_gh_api):
        form_body = 'submissionType=edit-format&puid=fmt/1&identifierType=testType&identifierText=testText'
        signature = {'identifiers': [{'identifierText': 'existingText', 'identifierType': 'existingType'}]}
        pr_file_content = self.get_pr_file_contents(mock_gh_api, form_body, signature, {})
        identifiers = pr_file_content['identifiers']
        self.assertEqual(len(identifiers), 2)
        self.assertEqual(identifiers[0]['identifierText'], 'existingText')
        self.assertEqual(identifiers[0]['identifierType'], 'existingType')
        self.assertEqual(identifiers[1]['identifierText'], 'testText')
        self.assertEqual(identifiers[1]['identifierType'], 'testType')

    @patch('lambdas.submissions.GhApi')
    @patch('boto3.client')
    def test_edit_add_to_missing_relationships(self, _, mock_gh_api):
        form_body = 'submissionType=edit-format&puid=fmt/1&relationshipType=testType&relatedFormatName=fmt/1'
        pr_file_content = self.get_pr_file_contents(mock_gh_api, form_body, {'fileFormatID': 1}, {})
        relationships = pr_file_content['relationships']
        self.assertEqual(len(relationships), 1)
        self.assertEqual(relationships[0]['relatedFormatID'], 1)
        self.assertEqual(relationships[0]['relationshipType'], 'testType')

    @patch('lambdas.submissions.GhApi')
    @patch('boto3.client')
    def test_edit_add_to_existing_relationships(self, _, mock_gh_api):
        form_body = 'submissionType=edit-format&puid=fmt/1&relationshipType=testType&relatedFormatName=fmt/1'
        signature = {'fileFormatID': 1, 'relationships': [{'relatedFormatID': 2, 'relationshipType': 'existingType'}]}
        pr_file_content = self.get_pr_file_contents(mock_gh_api, form_body, signature, {})
        relationships = pr_file_content['relationships']
        self.assertEqual(len(relationships), 2)
        self.assertEqual(relationships[0]['relatedFormatID'], 2)
        self.assertEqual(relationships[0]['relationshipType'], 'existingType')
        self.assertEqual(relationships[1]['relatedFormatID'], 1)
        self.assertEqual(relationships[1]['relationshipType'], 'testType')

    @patch('lambdas.submissions.GhApi')
    @patch('boto3.client')
    def test_return_error_if_relationship_name_does_not_exist(self, _, mock_gh_api):
        form_body = 'submissionType=edit-format&puid=fmt/1&relationshipType=testType&relatedFormatName=fmt/10'
        signature = {'fileFormatID': 1}
        with self.assertRaises(ValueError) as err:
            self.get_pr_file_contents(mock_gh_api, form_body, signature, {})
        self.assertEqual(err.exception.args[0], 'fmt/10 does not exist')

    @patch('lambdas.submissions.GhApi')
    @patch('boto3.client')
    def test_add_new_actors_field(self, _, mock_gh_api):
        for field_value in ["0", "2"]:
            for actor_field in ['developedBy', 'supportedBy']:
                with self.subTest(actor_field):
                    mock_gh_api.reset_mock()
                    form_body = f'submissionType=edit-format&puid=fmt/1&{actor_field}={field_value}'
                    signature = {}
                    if field_value == "0":
                        self.assert_pr_not_created(mock_gh_api, form_body, signature, {})
                    else:
                        pr_file_contents = self.get_pr_file_contents(mock_gh_api, form_body, signature, {})
                        self.assertEqual(pr_file_contents[actor_field], int(field_value))

    @patch('lambdas.submissions.GhApi')
    @patch('boto3.client')
    def test_update_existing_actors_field(self, _, mock_gh_api):
        for field_value in ["0", "2"]:
            for actor_field in ['developedBy', 'supportedBy']:
                with self.subTest(actor_field):
                    mock_gh_api.reset_mock()
                    form_body = f'submissionType=edit-format&puid=fmt/1&{actor_field}={field_value}'
                    signature = {actor_field: 1}
                    if field_value == "0":
                        self.assert_pr_not_created(mock_gh_api, form_body, signature, {})
                    else:
                        pr_file_contents = self.get_pr_file_contents(mock_gh_api, form_body, signature, {})
                        self.assertEqual(pr_file_contents[actor_field], int(field_value))

    @patch('lambdas.submissions.GhApi')
    @patch('boto3.client')
    def test_add_actor(self, _, mock_gh_api):
        form_body = ('submissionType=add-actor&name=testName&address=testAddress&addressCountry=GBR'
                     '&companyWebsite=https://example.com&supportWebsite=https://example.com')
        pr_file_contents = self.get_pr_file_contents(mock_gh_api, form_body, {}, {})
        self.assertEqual(pr_file_contents['name'], 'testName')
        self.assertEqual(pr_file_contents['address'], 'testAddress')
        self.assertEqual(pr_file_contents['addressCountry'], 'GBR')
        self.assertEqual(pr_file_contents['supportWebsite'], 'https://example.com')
        self.assertEqual(pr_file_contents['companyWebsite'], 'https://example.com')

    @patch('lambdas.submissions.GhApi')
    @patch('boto3.client')
    def test_edit_actor_change_existing_property(self, _, mock_gh_api):
        form_body = 'submissionType=edit-actor&name=testName&actorId=1'
        pr_file_contents = self.get_pr_file_contents(mock_gh_api, form_body, {}, {'name': 'originalName'})
        self.assertEqual(pr_file_contents['name'], 'testName')

    @patch('lambdas.submissions.GhApi')
    @patch('boto3.client')
    def test_edit_actor_add_new_property(self, _, mock_gh_api):
        form_body = 'submissionType=edit-actor&address=testAddress&actorId=1'
        pr_file_contents = self.get_pr_file_contents(mock_gh_api, form_body, {}, {'name': 'testName'})
        self.assertEqual(pr_file_contents['name'], 'testName')
        self.assertEqual(pr_file_contents['address'], 'testAddress')

    @patch('lambdas.submissions.GhApi')
    @patch('boto3.client')
    def test_edit_actor_returns_error_if_actor_does_not_exist(self, _, mock_gh_api):
        form_body = 'submissionType=edit-actor&address=testAddress&actorId=10'
        with self.assertRaises(KeyError) as err:
            self.get_pr_file_contents(mock_gh_api, form_body, {}, {})
        self.assertEqual(err.exception.args[0], '10.json')

    @patch('lambdas.submissions.GhApi')
    @patch('boto3.client')
    def test_add_format_adds_a_new_format_without_signature(self, _, mock_gh_api):
        form_body = 'submissionType=add-format&formatName=testName&formatTypes=testType&formatDisclosure=Full'
        pr_file_contents = self.get_pr_file_contents(mock_gh_api, form_body, {}, {})
        self.assertEqual(pr_file_contents['formatName'], 'testName')
        self.assertEqual(pr_file_contents['formatTypes'], 'testType')
        self.assertEqual(pr_file_contents['formatDisclosure'], 'Full')

    @patch('lambdas.submissions.GhApi')
    @patch('boto3.client')
    def test_add_format_adds_a_new_format_with_signature(self, _, mock_gh_api):
        form_body = ('submissionType=add-format&signature-byteSequence=testSequence&signature-maxOffset=0&signature'
                     '-endianness=Little-endian')
        pr_file_contents = self.get_pr_file_contents(mock_gh_api, form_body, {}, {})
        signatures = pr_file_contents['internalSignatures'][0]
        self.assertEqual(signatures['byteSequence'], 'testSequence')
        self.assertEqual(signatures['maxOffset'], 0)
        self.assertEqual(signatures['endianness'], 'Little-endian')

    @patch('lambdas.submissions.GhApi')
    @patch('boto3.client')
    def test_correct_change_description_is_used_to_create_pr(self, _, mock_gh_api):
        for change_description in ['A change', None]:
            with self.subTest(change_description):
                mock_gh_api.reset_mock()
                description_request = f'&changeDescription={change_description}' if change_description else ''
                form_body = 'submissionType=add-format' + description_request
                mock_instance = self.run_lambda(mock_gh_api, form_body, {}, {})
                pr_args = mock_instance.pulls.create.mock_calls[0].kwargs
                self.assertEqual(pr_args['base'], 'develop')
                self.assertEqual(pr_args['body'], 'New submission' if not change_description else change_description)

    @patch('lambdas.submissions.GhApi')
    @patch('boto3.client')
    def test_add_sha_if_file_exists(self, _, mock_gh_api):
        form_body = 'submissionType=add-format'
        mock_instance = mock_gh_api.return_value
        mock_instance.repos.download_zipball_archive.return_value = self.create_zip_file({}, {})
        mock_instance.repos.get_content.return_value = {'sha': 'testSha'}
        submissions.lambda_handler({'body': form_body}, None)
        pr_args = mock_instance.repos.create_or_update_file_contents.mock_calls[0].kwargs
        self.assertEqual(pr_args['sha'], 'testSha')

    @patch('lambdas.submissions.GhApi')
    @patch('boto3.client')
    def test_no_sha_if_file_does_not_exist(self, _, mock_gh_api):
        form_body = 'submissionType=add-format'
        mock_instance = mock_gh_api.return_value
        mock_instance.repos.download_zipball_archive.return_value = self.create_zip_file({}, {})
        mock_instance.repos.get_content.side_effect = HTTPError("url", "", "", "", None)
        submissions.lambda_handler({'body': form_body}, None)
        pr_args = mock_instance.repos.create_or_update_file_contents.mock_calls[0].kwargs
        self.assertIsNone(pr_args.get('sha'))

    @patch('lambdas.submissions.GhApi')
    @patch('boto3.client')
    def test_author_set_to_contributor_name(self, _, mock_gh_api):
        form_body = 'submissionType=add-format&contributorName=testContributor'
        mock_instance = self.run_lambda(mock_gh_api, form_body, {}, {})
        pr_args = mock_instance.repos.create_or_update_file_contents.mock_calls[0].kwargs
        self.assertEqual(pr_args['author']['name'], 'testContributor')

    @patch('lambdas.submissions.GhApi')
    @patch('boto3.client')
    def test_author_set_to_tna(self, _, mock_gh_api):
        form_body = 'submissionType=add-format'
        mock_instance = self.run_lambda(mock_gh_api, form_body, {}, {})
        pr_args = mock_instance.repos.create_or_update_file_contents.mock_calls[0].kwargs
        self.assertEqual(pr_args['author']['name'], 'The National Archives')

    @patch('lambdas.submissions.GhApi')
    @patch('boto3.client')
    def test_error_with_invalid_submission_type(self, _, mock_gh_api):
        form_body = 'submissionType=invalid'
        mock_instance = mock_gh_api.return_value
        mock_instance.repos.download_zipball_archive.return_value = self.create_zip_file({}, {})
        response = submissions.lambda_handler({'body': form_body}, None)
        self.assertEqual(response['statusCode'], 500)
        self.assertEqual(response['body'], 'An error occurred: submissionType invalid not found')
