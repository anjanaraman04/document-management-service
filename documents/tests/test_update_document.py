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

    def patch(self, search, replacement, occurrence=None):
        body = {'search': search, 'replacement': replacement}
        if occurrence is not None:
            body['occurrence'] = occurrence
        return self.client.patch(
            self.url,
            data=json.dumps(body),
            content_type='application/json',
        )

    def test_replace_all_occurrences(self):
        response = self.patch('hello', 'hi')
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertNotIn('hello', body['content'])
        self.assertEqual(body['content'].count('hi'), 2)

    def test_replace_specific_occurrence(self):
        response = self.patch('hello', 'hi', occurrence=0)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        # Only the first 'hello' is replaced
        self.assertIn('hi', body['content'])
        self.assertIn('hello', body['content'])

    def test_replace_increments_version(self):
        original_version = self.document.version
        response = self.patch('bob', 'alice')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['version'], original_version + 1)

    def test_search_term_not_found_returns_404(self):
        response = self.patch('nonexistent', 'something')
        self.assertEqual(response.status_code, 404)
        self.assertIn('error', response.json())

    def test_occurrence_out_of_range_returns_400(self):
        response = self.patch('hello', 'hi', occurrence=99)
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_missing_search_returns_400(self):
        response = self.client.patch(
            self.url,
            data=json.dumps({'replacement': 'hi'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_missing_replacement_returns_400(self):
        response = self.client.patch(
            self.url,
            data=json.dumps({'search': 'hello'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_invalid_json_returns_400(self):
        response = self.client.patch(
            self.url,
            data='not valid json',
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_non_existent_document_returns_404(self):
        response = self.client.patch(
            '/api/documents/99999/replace-text/',
            data=json.dumps({'search': 'hello', 'replacement': 'hi'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 404)
        self.assertIn('error', response.json())
