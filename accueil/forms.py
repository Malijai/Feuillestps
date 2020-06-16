# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django import forms
from .models import User, Contratippm, Employe, Projet
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


ContratFormSet = inlineformset_factory(User, Contratippm, form= ContratippmForm,
                                         extra=2, can_delete=True)

