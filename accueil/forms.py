# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django import forms
from .models import User, Contratippm, Employe, Projet, Tempsfacture
from django.forms import inlineformset_factory


class EmployeForm(forms.ModelForm):
    class Meta:
        model = Employe
        fields = ('numeemploye','signature')
        exclude = ()


class ContratippmForm(forms.ModelForm):
    class Meta:
        model = Contratippm
        fields = ('numcontrat','projet','maxheures','datedebut','datefin','role','tauxhoraire','niveau','vacancestaux')
        help_texts = {
            'datedebut': 'aaaa-mm-jj',
            'datefin': 'aaaa-mm-jj',
        }
        exclude = ()


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['last_name', 'first_name', 'email']
        exclude = ()


class ProjetForm(forms.ModelForm):
    class Meta:
        model = Projet
        fields = ('nomcourt','nomlong', 'budget', 'origine', 'responsable')

class TempsForm(forms.ModelForm):
    class Meta:
        model = Tempsfacture
        fields = ('partemployeurcorr', )
        exclude = ('correction','partemployeur','bonneperiode','heures', 'contrat',)


class EvaluationForm(forms.Form):
    datedebut = forms.DateField(label='Date de debut')
    datefin = forms.DateField(label='Date de fin')
    heuressemaine = forms.IntegerField(label="Nombre maximum d'heures par semaine")
    tauxhoraire = forms.DecimalField(label='Taux horaire')
    tauxvacances = forms.DecimalField(label='% de vacances', help_text="Rentrer 4 pour 4%")


ContratFormSet = inlineformset_factory(User, Contratippm, form= ContratippmForm,
                                         extra=2, can_delete=True)

