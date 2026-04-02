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

    def test_query_with_match_returns_matches(self):
        response = self.client.get(self.url, {'q': 'bob'})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body['query'], 'bob')
        self.assertIn('matches', body)
        self.assertGreater(body['total'], 0)

    def test_match_contains_expected_fields(self):
        response = self.client.get(self.url, {'q': 'bob'})
        match = response.json()['matches'][0]
        self.assertIn('occurrence', match)
        self.assertIn('position', match)
        self.assertIn('snippet', match)
        self.assertIn('match_text', match)

    def test_snippet_contains_matched_term(self):
        response = self.client.get(self.url, {'q': 'bob'})
        snippet = response.json()['matches'][0]['snippet']
        self.assertIn('bob', snippet)

    def test_query_with_no_match_returns_404(self):
        response = self.client.get(self.url, {'q': 'elephant'})
        self.assertEqual(response.status_code, 404)
        self.assertIn('error', response.json())

    def test_search_is_case_insensitive(self):
        response_lower = self.client.get(self.url, {'q': 'hello'})
        response_upper = self.client.get(self.url, {'q': 'HELLO'})
        response_mixed = self.client.get(self.url, {'q': 'Hello'})
        self.assertEqual(response_lower.status_code, 200)
        self.assertEqual(response_upper.status_code, 200)
        self.assertEqual(response_mixed.status_code, 200)

    def test_multiple_occurrences_all_returned(self):
        doc = Document.objects.create(
            title='Repeat Doc',
            content='cat and cat and cat',
        )
        response = self.client.get(f'/api/documents/{doc.pk}/search/', {'q': 'cat'})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body['total'], 3)
        self.assertEqual(len(body['matches']), 3)

    def test_occurrence_index_is_zero_based_and_sequential(self):
        doc = Document.objects.create(
            title='Repeat Doc',
            content='cat and cat and cat',
        )
        response = self.client.get(f'/api/documents/{doc.pk}/search/', {'q': 'cat'})
        occurrences = [m['occurrence'] for m in response.json()['matches']]
        self.assertEqual(occurrences, [0, 1, 2])

    def test_substring_match_within_word(self):
        # Substring search should match 'test' inside 'testing'
        doc = Document.objects.create(title='Sub Doc', content='testing the test')
        response = self.client.get(f'/api/documents/{doc.pk}/search/', {'q': 'test'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['total'], 2)

    def test_common_word_returns_match(self):
        response = self.client.get(self.url, {'q': 'is'})
        self.assertEqual(response.status_code, 200)
        self.assertGreater(response.json()['total'], 0)

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
