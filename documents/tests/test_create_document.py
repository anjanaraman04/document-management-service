import json
from django.test import TestCase, Client
from documents.models import Document


class CreateDocumentTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = '/api/documents/'

    def post(self, data):
        return self.client.patch(
            self.url,
            data=json.dumps(data),
            content_type='application/json',
        )

    def test_valid_document_creates_successfully(self):
        response = self.client.post(
            self.url,
            data=json.dumps({'title': 'Test Doc', 'content': 'Hello world'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(body['title'], 'Test Doc')
        self.assertEqual(body['content'], 'Hello world')
        self.assertEqual(body['version'], 1)
        self.assertIn('id', body)
        self.assertIn('created_at', body)
        self.assertIn('updated_at', body)
        self.assertTrue(Document.objects.filter(pk=body['id']).exists())

    def test_missing_title_returns_400(self):
        response = self.client.post(
            self.url,
            data=json.dumps({'content': 'Hello world'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_missing_content_returns_400(self):
        response = self.client.post(
            self.url,
            data=json.dumps({'title': 'Test Doc'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_missing_both_fields_returns_400(self):
        response = self.client.post(
            self.url,
            data=json.dumps({}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_empty_content_returns_400(self):
        response = self.client.post(
            self.url,
            data=json.dumps({'title': 'Test Doc', 'content': ''}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_empty_title_returns_400(self):
        response = self.client.post(
            self.url,
            data=json.dumps({'title': '', 'content': 'Hello world'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_very_large_content_creates_successfully(self):
        large_content = 'word ' * 100_000  # ~500KB of text
        response = self.client.post(
            self.url,
            data=json.dumps({'title': 'Large Doc', 'content': large_content}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 201)
        body = response.json()
        document = Document.objects.get(pk=body['id'])
        self.assertEqual(document.content, large_content)

    def test_duplicate_titles_both_create_successfully(self):
        payload = {'title': 'Duplicate Title', 'content': 'First document'}
        response1 = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json',
        )
        response2 = self.client.post(
            self.url,
            data=json.dumps({**payload, 'content': 'Second document'}),
            content_type='application/json',
        )
        self.assertEqual(response1.status_code, 201)
        self.assertEqual(response2.status_code, 201)
        self.assertNotEqual(response1.json()['id'], response2.json()['id'])
        self.assertEqual(Document.objects.filter(title='Duplicate Title').count(), 2)
