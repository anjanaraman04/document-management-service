from django.test import TestCase, Client
from documents.models import Document, DocumentChange


class DeleteDocumentTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.document = Document.objects.create(
            title='Test Doc',
            content='Hello this is my first document.',
        )
        self.url = f'/api/documents/{self.document.pk}/delete/'

    def test_delete_returns_200(self):
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body['status'], 'deleted')
        self.assertEqual(body['id'], self.document.pk)

    def test_document_is_removed_from_database(self):
        self.client.delete(self.url)
        self.assertFalse(Document.objects.filter(pk=self.document.pk).exists())

    def test_associated_changes_are_deleted(self):
        DocumentChange.objects.create(
            document=self.document,
            original_text='Hello',
            replacement_text='Hi',
            position=0,
            version_at_change=1,
        )
        self.client.delete(self.url)
        self.assertFalse(DocumentChange.objects.filter(document_id=self.document.pk).exists())

    def test_non_existent_document_returns_404(self):
        response = self.client.delete('/api/documents/99999/delete/')
        self.assertEqual(response.status_code, 404)
        self.assertIn('error', response.json())
