import time
from django.test import TestCase, Client
from documents.models import Document


class ViewDocumentTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.document = Document.objects.create(
            title='Test Doc',
            content='Hello my name is bob. I like cheese.',
        )
        self.url = f'/documents/{self.document.pk}/'

    def test_existing_document_returns_200(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_non_existent_document_returns_404(self):
        response = self.client.get('/documents/99999/')
        self.assertEqual(response.status_code, 404)

    def test_response_shape_is_correct(self):
        response = self.client.get(self.url)
        self.assertContains(response, self.document.title)
        self.assertContains(response, self.document.content)
        self.assertContains(response, f'v{self.document.version}')

    def test_large_document_retrieval_is_acceptable(self):
        large_content = 'word ' * 100_000  # ~500KB of text
        doc = Document.objects.create(title='Large Doc', content=large_content)

        start = time.time()
        response = self.client.get(f'/documents/{doc.pk}/')
        elapsed = time.time() - start

        self.assertEqual(response.status_code, 200)
        self.assertLess(elapsed, 2.0, 'Large document retrieval took too long')
