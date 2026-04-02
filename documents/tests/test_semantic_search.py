import torch
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from documents.models import Document


class SemanticSearchTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.document = Document.objects.create(
            title='Test Doc',
            content='The cat sat on the mat. The dog ran in the park. I enjoy eating pizza.',
        )
        self.url = f'/api/documents/{self.document.pk}/semantic-search/'

    def _patch_model(self, scores):
        """
        Patch the model and cos_sim so tests run without downloading weights.
        - get_model returns a mock whose encode() returns a zero tensor.
        - sentence_transformers.util.cos_sim returns a tensor built from `scores`.
        """
        patcher_model = patch(
            'documents.views.DocumentSemanticSearchView.get_model'
        )
        patcher_cos_sim = patch('sentence_transformers.util.cos_sim')

        mock_get_model = patcher_model.start()
        mock_cos_sim = patcher_cos_sim.start()

        mock_model = MagicMock()
        mock_model.encode.return_value = torch.zeros(384)
        mock_get_model.return_value = mock_model

        mock_cos_sim.return_value = torch.tensor([scores])

        self.addCleanup(patcher_model.stop)
        self.addCleanup(patcher_cos_sim.stop)

    def test_returns_200_with_results(self):
        self._patch_model([0.9, 0.5, 0.2])
        response = self.client.get(self.url, {'q': 'cat'})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn('results', body)
        self.assertGreater(len(body['results']), 0)

    def test_results_contain_expected_fields(self):
        self._patch_model([0.9, 0.5, 0.2])
        response = self.client.get(self.url, {'q': 'cat'})
        result = response.json()['results'][0]
        self.assertIn('rank', result)
        self.assertIn('score', result)
        self.assertIn('text', result)

    def test_results_are_ranked_highest_score_first(self):
        self._patch_model([0.2, 0.9, 0.5])
        response = self.client.get(self.url, {'q': 'dog'})
        results = response.json()['results']
        scores = [r['score'] for r in results]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_returns_at_most_five_results(self):
        self._patch_model([0.9, 0.7, 0.5])
        response = self.client.get(self.url, {'q': 'anything'})
        self.assertLessEqual(len(response.json()['results']), 5)

    def test_response_contains_query_and_id(self):
        self._patch_model([0.9, 0.5, 0.2])
        response = self.client.get(self.url, {'q': 'cat'})
        body = response.json()
        self.assertEqual(body['id'], self.document.pk)
        self.assertEqual(body['query'], 'cat')

    def test_missing_query_param_returns_400(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_empty_query_returns_400(self):
        response = self.client.get(self.url, {'q': ''})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_non_existent_document_returns_404(self):
        response = self.client.get('/api/documents/99999/semantic-search/', {'q': 'cat'})
        self.assertEqual(response.status_code, 404)
        self.assertIn('error', response.json())

    def test_score_is_between_zero_and_one(self):
        self._patch_model([0.75, 0.4, 0.1])
        response = self.client.get(self.url, {'q': 'cat'})
        for result in response.json()['results']:
            self.assertGreaterEqual(result['score'], 0.0)
            self.assertLessEqual(result['score'], 1.0)

    def test_rank_starts_at_one_and_is_sequential(self):
        self._patch_model([0.9, 0.5, 0.2])
        response = self.client.get(self.url, {'q': 'cat'})
        ranks = [r['rank'] for r in response.json()['results']]
        self.assertEqual(ranks, list(range(1, len(ranks) + 1)))
