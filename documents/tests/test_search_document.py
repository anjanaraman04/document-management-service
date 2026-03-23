from django.test import TestCase, Client
from documents.models import Document


class SearchDocumentTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.document = Document.objects.create(
            title='Test Doc',
            content='Hello my name is bob. I like cheese and pizza.',
        )
        self.url = f'/api/documents/{self.document.pk}/search/'

    def test_query_with_match_returns_snippet(self):
        response = self.client.get(self.url, {'q': 'bob'})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body['query'], 'bob')
        self.assertIn('snippet', body)
        self.assertIn('bob', body['snippet'])

    def test_query_with_no_match_returns_404(self):
        response = self.client.get(self.url, {'q': 'elephant'})
        self.assertEqual(response.status_code, 404)
        self.assertIn('error', response.json())

    def test_search_is_case_insensitive(self):
        # FTS5 with the default unicode61 tokenizer is case-insensitive
        response_lower = self.client.get(self.url, {'q': 'hello'})
        response_upper = self.client.get(self.url, {'q': 'HELLO'})
        response_mixed = self.client.get(self.url, {'q': 'Hello'})
        self.assertEqual(response_lower.status_code, 200)
        self.assertEqual(response_upper.status_code, 200)
        self.assertEqual(response_mixed.status_code, 200)

    def test_punctuation_is_stripped_from_tokens(self):
        # FTS5 treats punctuation as token boundaries, so 'bob.' in the
        # content is indexed as the token 'bob' — searching 'bob' matches it
        doc = Document.objects.create(
            title='Punct Doc',
            content='hello bob. how are you?',
        )
        response = self.client.get(f'/api/documents/{doc.pk}/search/', {'q': 'bob'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('bob', response.json()['snippet'])

    def test_special_characters_in_query_are_handled(self):
        # Characters like *, -, " have special meaning in FTS5 queries.
        # Django passes them as-is to SQLite; an invalid FTS5 expression
        # raises an OperationalError which should surface as a 400.
        response = self.client.get(self.url, {'q': '***'})
        self.assertIn(response.status_code, [400, 404])

    def test_very_common_word_returns_match(self):
        # FTS5 has no stop-word list by default, so common words like 'is'
        # are indexed and searchable
        response = self.client.get(self.url, {'q': 'is'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('snippet', response.json())

    def test_non_existent_document_returns_404(self):
        response = self.client.get('/api/documents/99999/search/', {'q': 'bob'})
        self.assertEqual(response.status_code, 404)
        self.assertIn('error', response.json())

    def test_empty_query_returns_400(self):
        response = self.client.get(self.url, {'q': ''})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_missing_query_param_returns_400(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())
