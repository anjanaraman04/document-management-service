from django.urls import path
from .views import DocumentCreateView, DocumentDetailView, DocumentCrossSearchView, DocumentSearchView, DocumentReplaceTextView, DocumentSemanticSearchView, DocumentChangesView, DocumentChangeAcceptView, DocumentChangeRejectView, DocumentDeleteView

urlpatterns = [
    path('', DocumentCreateView.as_view(), name='document-create'),
    path('search/', DocumentCrossSearchView.as_view(), name='document-cross-search'),
    path('<int:pk>/', DocumentDetailView.as_view(), name='document-detail'),
    path('<int:pk>/search/', DocumentSearchView.as_view(), name='document-search'),
    path('<int:pk>/replace-text/', DocumentReplaceTextView.as_view(), name='document-replace-text'),
    path('<int:pk>/semantic-search/', DocumentSemanticSearchView.as_view(), name='document-semantic-search'),
    path('<int:pk>/changes/', DocumentChangesView.as_view(), name='document-changes'),
    path('<int:pk>/changes/<int:change_id>/accept/', DocumentChangeAcceptView.as_view(), name='document-change-accept'),
    path('<int:pk>/changes/<int:change_id>/reject/', DocumentChangeRejectView.as_view(), name='document-change-reject'),
    path('<int:pk>/delete/', DocumentDeleteView.as_view(), name='document-delete'),
]
