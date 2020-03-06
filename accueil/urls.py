from django.urls import path
from .views import fdetemps, choix, listeassistants, assistant_edit, bilan, listecontrats


urlpatterns = [
    path('fdt/', fdetemps, name='do_fdt'),
    path('choix/', choix, name='choix'),
    path('liste/', listeassistants, name='listeassistants'),
    path('assistant/<int:pk>/', assistant_edit, name='assistant_edit'),
    path('bilan/<int:pk>/<int:cid>/', bilan, name='bilan'),
    path('listecontrats/', listecontrats, name='listecontrats'),

]

#url(r'^new/$', creerdossier, name='creerdossier'),
