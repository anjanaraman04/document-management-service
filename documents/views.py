import json
import re
from django.db import connection
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from .models import Document, DocumentChange


@method_decorator(csrf_exempt, name='dispatch')
class DocumentCreateView(View):
    def post(self, request):
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        title = body.get('title')
        content = body.get('content')

        if not title or not content:
            return JsonResponse({'error': 'Both "title" and "content" fields are required'}, status=400)

        document = Document.objects.create(
            title=title,
            content=content,
        )

        return JsonResponse({
            'id': document.pk,
            'title': document.title,
            'content': document.content,
            'version': document.version,
            'created_at': document.created_at.isoformat(),
            'updated_at': document.updated_at.isoformat(),
        }, status=201)


@method_decorator(csrf_exempt, name='dispatch')
class DocumentDetailView(View):
    def get(self, request, pk):
        try:
            document = Document.objects.get(pk=pk)
        except Document.DoesNotExist:
            return JsonResponse({'error': 'Document not found'}, status=404)

        return JsonResponse({
            'id': document.pk,
            'title': document.title,
            'content': document.content,
            'version': document.version,
            'created_at': document.created_at.isoformat(),
            'updated_at': document.updated_at.isoformat(),
        })


def extract_snippet(content, query, index=None, padding=50):
    if index is None:
        index = content.lower().find(query.lower())
    if index == -1:
        return None
    start = max(0, index - padding)
    end = min(len(content), index + len(query) + padding)
    snippet = content[start:end]
    match = content[index:index + len(query)]
    snippet = snippet.replace(match, f'>>>{match}<<<', 1)
    return snippet


@method_decorator(csrf_exempt, name='dispatch')
class DocumentCrossSearchView(View):
    def get(self, request):
        query = request.GET.get('q', '').strip()
        if not query:
            return JsonResponse({'error': 'Query parameter "q" is required'}, status=400)

        documents = Document.objects.filter(content__icontains=query)

        if not documents.exists():
            return JsonResponse({'error': f'"{query}" not found in any document'}, status=404)

        results = []
        for doc in documents:
            matches = []
            content_lower = doc.content.lower()
            query_lower = query.lower()
            offset = 0
            while True:
                pos = content_lower.find(query_lower, offset)
                if pos == -1:
                    break
                matches.append({
                    'occurrence': len(matches),
                    'position': pos,
                    'snippet': extract_snippet(doc.content, query, pos),
                })
                offset = pos + len(query)
            results.append({'id': doc.pk, 'title': doc.title, 'matches': matches})

        return JsonResponse({'query': query, 'results': results})


@method_decorator(csrf_exempt, name='dispatch')
class DocumentSearchView(View):
    def get(self, request, pk):
        try:
            document = Document.objects.get(pk=pk)
        except Document.DoesNotExist:
            return JsonResponse({'error': 'Document not found'}, status=404)

        query = request.GET.get('q', '').strip()
        if not query:
            return JsonResponse({'error': 'Query parameter "q" is required'}, status=400)

        content = document.content
        query_lower = query.lower()
        content_lower = content.lower()

        matches = []
        offset = 0
        while True:
            pos = content_lower.find(query_lower, offset)
            if pos == -1:
                break
            snippet = extract_snippet(content, query, padding=40)
            matches.append({
                'occurrence': len(matches),
                'position': pos,
                'snippet': snippet,
                'match_text': content[pos:pos + len(query)],
            })
            offset = pos + len(query)

        if not matches:
            return JsonResponse({'error': f'"{query}" not found in document'}, status=404)

        return JsonResponse({
            'id': document.pk,
            'query': query,
            'total': len(matches),
            'matches': matches,
        })


@method_decorator(csrf_exempt, name='dispatch')
class DocumentReplaceTextView(View):
    def patch(self, request, pk):
        try:
            document = Document.objects.get(pk=pk)
        except Document.DoesNotExist:
            return JsonResponse({'error': 'Document not found'}, status=404)

        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        search = body.get('search')
        replacement = body.get('replacement')
        occurrence = body.get('occurrence')  # optional 0-based index

        if not search or replacement is None:
            return JsonResponse({'error': '"search" and "replacement" are required'}, status=400)

        if search not in document.content:
            return JsonResponse({'error': f'"{search}" not found in document'}, status=404)

        # Collect all positions of the search term
        positions = []
        offset = 0
        while True:
            pos = document.content.find(search, offset)
            if pos == -1:
                break
            positions.append(pos)
            offset = pos + len(search)

        if occurrence is not None:
            if occurrence >= len(positions):
                return JsonResponse(
                    {'error': f'Occurrence {occurrence} does not exist (found {len(positions)})'},
                    status=400,
                )
            target_pos = positions[occurrence]
            DocumentChange.objects.create(
                document=document,
                original_text=search,
                replacement_text=replacement,
                position=target_pos,
                version_at_change=document.version,
            )
            document.content = (
                document.content[:target_pos]
                + replacement
                + document.content[target_pos + len(search):]
            )
        else:
            for pos in positions:
                DocumentChange.objects.create(
                    document=document,
                    original_text=search,
                    replacement_text=replacement,
                    position=pos,
                    version_at_change=document.version,
                )
            document.content = document.content.replace(search, replacement)

        document.version += 1
        document.save()

        return JsonResponse({
            'id': document.pk,
            'title': document.title,
            'content': document.content,
            'version': document.version,
            'created_at': document.created_at.isoformat(),
            'updated_at': document.updated_at.isoformat(),
        })


@method_decorator(csrf_exempt, name='dispatch')
class DocumentSemanticSearchView(View):
    _model = None

    @classmethod
    def get_model(cls):
        if cls._model is None:
            from sentence_transformers import SentenceTransformer
            cls._model = SentenceTransformer('all-MiniLM-L6-v2')
        return cls._model

    def get(self, request, pk):
        try:
            document = Document.objects.get(pk=pk)
        except Document.DoesNotExist:
            return JsonResponse({'error': 'Document not found'}, status=404)

        query = request.GET.get('q', '').strip()
        if not query:
            return JsonResponse({'error': 'Query parameter "q" is required'}, status=400)

        # Split into sentences (by ". ", "! ", "? ", or newlines)
        raw_chunks = re.split(r'(?<=[.!?])\s+|\n+', document.content)
        chunks = [c.strip() for c in raw_chunks if c.strip()]

        if not chunks:
            return JsonResponse({'error': 'Document has no content to search'}, status=400)

        from sentence_transformers import util
        import torch

        model = self.get_model()
        query_embedding = model.encode(query, convert_to_tensor=True)
        chunk_embeddings = model.encode(chunks, convert_to_tensor=True)

        scores = util.cos_sim(query_embedding, chunk_embeddings)[0]
        top_k = min(5, len(chunks))
        top_indices = torch.topk(scores, k=top_k).indices.tolist()

        results = [
            {
                'rank': i + 1,
                'score': round(float(scores[idx]), 4),
                'text': chunks[idx],
            }
            for i, idx in enumerate(top_indices)
        ]

        return JsonResponse({
            'id': document.pk,
            'query': query,
            'results': results,
        })


@method_decorator(csrf_exempt, name='dispatch')
class DocumentChangesView(View):
    def get(self, request, pk):
        try:
            document = Document.objects.get(pk=pk)
        except Document.DoesNotExist:
            return JsonResponse({'error': 'Document not found'}, status=404)

        changes = document.changes.all()

        return JsonResponse({
            'id': document.pk,
            'version': document.version,
            'changes': [
                {
                    'id': c.pk,
                    'original_text': c.original_text,
                    'replacement_text': c.replacement_text,
                    'position': c.position,
                    'version_at_change': c.version_at_change,
                    'created_at': c.created_at.isoformat(),
                }
                for c in changes
            ],
        })


@method_decorator(csrf_exempt, name='dispatch')
class DocumentChangeAcceptView(View):
    def post(self, request, pk, change_id):
        try:
            change = DocumentChange.objects.get(pk=change_id, document_id=pk)
        except DocumentChange.DoesNotExist:
            return JsonResponse({'error': 'Change not found'}, status=404)

        # Accepting a change simply removes it from the log — the replacement
        # is already applied to the document content, so no content change needed.
        change.delete()

        return JsonResponse({'status': 'accepted', 'change_id': change_id})


@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(csrf_exempt, name='dispatch')
class DocumentDeleteView(View):
    def delete(self, request, pk):
        try:
            document = Document.objects.get(pk=pk)
        except Document.DoesNotExist:
            return JsonResponse({'error': 'Document not found'}, status=404)
        document.delete()
        return JsonResponse({'status': 'deleted', 'id': pk})


class DocumentChangeRejectView(View):
    def post(self, request, pk, change_id):
        try:
            change = DocumentChange.objects.get(pk=change_id, document_id=pk)
        except DocumentChange.DoesNotExist:
            return JsonResponse({'error': 'Change not found'}, status=404)

        document = change.document

        # Rejecting reverts the replacement back to the original text
        if change.replacement_text not in document.content:
            return JsonResponse({'error': 'Replacement text no longer found in document — cannot revert'}, status=400)

        document.content = document.content.replace(change.replacement_text, change.original_text, 1)
        document.version += 1
        document.save()
        change.delete()

        return JsonResponse({
            'status': 'rejected',
            'change_id': change_id,
            'content': document.content,
            'version': document.version,
        })
