from django.urls import path
from .views import fdetemps, choix, listeassistants, assistant_edit


urlpatterns = [
    path('fdt/', fdetemps, name='do_fdt'),
    path('choix/', choix, name='choix'),
    path('liste/', listeassistants, name='listeassistants'),
    path('assistant/<int:pk>/', assistant_edit, name='assistant_edit'),
]

#url(r'^new/$', creerdossier, name='creerdossier'),
