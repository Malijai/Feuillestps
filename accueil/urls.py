from django.urls import path
from .views import fdetemps, choix, listeassistants, assistant_edit, bilanparcontrat, listecontrats, \
    bilanparprojet, listeprojets, projet_new, mise_a_jour_db


urlpatterns = [
    path('fdt/', fdetemps, name='do_fdt'),
    path('choix/', choix, name='choix'),
    path('liste/', listeassistants, name='listeassistants'),
    path('assistant/<int:pk>/', assistant_edit, name='assistant_edit'),
    path('bcontrat/<int:cid>/', bilanparcontrat, name='bilanparcontrat'),
    path('bprojet/<int:pid>/', bilanparprojet, name='bilanparprojet'),
    path('listecontrats/', listecontrats, name='listecontrats'),
    path('projet/new/', projet_new, name='projet_new'),
    path('projet/', listeprojets, name='listeprojets'),
    path('correction/<int:pk>/', mise_a_jour_db, name='mise_a_jour_db'),

]

#url(r'^new/$', creerdossier, name='creerdossier'),
