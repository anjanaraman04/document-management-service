import json
from django.test import TestCase, Client
from documents.models import Document


class UpdateDocumentTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.document = Document.objects.create(
            title='Test Doc',
            content='hello my name is bob. hello i like cheese.',
        )
        self.url = f'/api/documents/{self.document.pk}/replace-text/'

    def patch(self, changes):
        return self.client.patch(
            self.url,
            data=json.dumps({'changes': changes}),
            content_type='application/json',
        )

    def test_one_valid_replacement_is_successful(self):
        response = self.patch([{'search': 'bob', 'replacement': 'alice'}])
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn('alice', body['content'])
        self.assertNotIn('bob', body['content'])
        self.assertEqual(body['warnings'], [])

    def test_multiple_replacements_applied_in_order(self):
        response = self.patch([
            {'search': 'hello', 'replacement': 'hi'},
            {'search': 'cheese', 'replacement': 'pizza'},
        ])
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn('hi', body['content'])
        self.assertIn('pizza', body['content'])
        self.assertNotIn('hello', body['content'])
        self.assertNotIn('cheese', body['content'])
        self.assertEqual(body['warnings'], [])

    def test_missing_target_text_returns_warning(self):
        response = self.patch([{'search': 'nonexistent', 'replacement': 'something'}])
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(len(body['warnings']), 1)
        self.assertIn('nonexistent', body['warnings'][0])

    def test_repeated_target_text_replaces_all_occurrences(self):
        # 'hello' appears twice in content
        response = self.patch([{'search': 'hello', 'replacement': 'hi'}])
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertNotIn('hello', body['content'])
        self.assertEqual(body['content'].count('hi'), 2)

    def test_overlapping_changes_first_replacement_affects_second(self):
        # 'bob' → 'alice', then 'alice' → 'charlie'
        # since changes apply sequentially, 'bob' becomes 'alice' then 'charlie'
        response = self.patch([
            {'search': 'bob', 'replacement': 'alice'},
            {'search': 'alice', 'replacement': 'charlie'},
        ])
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn('charlie', body['content'])
        self.assertNotIn('bob', body['content'])
        self.assertNotIn('alice', body['content'])

    def test_empty_changes_list_returns_400(self):
        response = self.patch([])
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_malformed_payload_missing_changes_key_returns_400(self):
        response = self.client.patch(
            self.url,
            data=json.dumps({'search': 'hello', 'replacement': 'hi'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_malformed_payload_invalid_json_returns_400(self):
        response = self.client.patch(
            self.url,
            data='not valid json',
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_malformed_change_missing_fields_returns_warning(self):
        response = self.patch([
            {'search': 'hello'},
            {'search': 'cheese', 'replacement': 'pizza'},
        ])
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(len(body['warnings']), 1)
        self.assertIn('pizza', body['content'])

    def test_non_existent_document_returns_404(self):
        response = self.client.patch(
            '/api/documents/99999/replace-text/',
            data=json.dumps({'changes': [{'search': 'hello', 'replacement': 'hi'}]}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 404)
        self.assertIn('error', response.json())
