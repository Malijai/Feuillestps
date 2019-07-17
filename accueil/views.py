from __future__ import unicode_literals
from django.shortcuts import render, redirect
from django.conf import settings
from django.http import HttpResponse
from django.contrib import messages
from .models import Tempsfacture, Contratippm, Role, User, Employe
from .forms import ContratFormSet, UserForm, EmployeForm
from reportlab.pdfgen.canvas import Canvas
from django.core.files.storage import FileSystemStorage
from reportlab.lib.utils import ImageReader
from reportlab.lib.pagesizes import letter
from django.contrib.auth.decorators import login_required
import datetime
import unicodedata
from textwrap import wrap

NOM_FICHIER_PDF = "FeuilleTemps_"
PAGE_INFO = "Feuilles de temps - Date d'impression : " + datetime.datetime.now().strftime('%d/%m/%Y')

DATE = datetime.datetime.now().strftime('%Y %b %d')


@login_required(login_url=settings.LOGIN_URI)
def listeassistants(request):
    assistants = Role.objects.filter(role=1).order_by('user__last_name')
    return render(request, 'liste.html', {'RAs': assistants})


@login_required(login_url=settings.LOGIN_URI)
def assistant_edit(request, pk):
    assistant = User.objects.get(pk=pk)
    employe = Employe.objects.get(user=assistant)
    if request.method == 'POST':
        assistant_form = UserForm(request.POST, instance=assistant)
        employe_form = EmployeForm(request.POST, request.FILES, instance=employe)
        if assistant_form.is_valid():
            assistant = assistant_form.save()
        if employe_form.is_valid():
            employe_form.save()
        contrat_formset = ContratFormSet(request.POST, request.FILES, instance=assistant)
        if contrat_formset.is_valid():
            contrat_formset.save()
            messages.success(request, "L'assistant et ses contrats ont été mis à jour.")
            if 'Savesurplace' in request.POST:
                return redirect(assistant_edit, assistant.id)
            else:
                return redirect('listeassistants')
        else:

            messages.error(request, "Il y a une erreur dans l'enregistrement de l'assistant ou du contrat.")
            return redirect(assistant_edit, assistant.id)
    else:
        assistant_form = UserForm(instance=assistant)
        employe_form = EmployeForm(instance=employe)
        contrat_formset = ContratFormSet(instance=assistant)

    context = {
        'form': assistant_form,
        'employe': employe_form,
        'contrat_formset': contrat_formset,
    }
    return render(request, "assistant_edit.html", context)


@login_required(login_url=settings.LOGIN_URI)
def choix(request):
    ra = False
    admin = False
    droits = Role.objects.filter(user_id=request.user.id)

    for droit in droits:
        if droit.role == Role.RA:
            ra = True
        elif droit.role == Role.ADMIN:
            admin = True

    return render(request, "choix.html",
                          {
                            'RA': ra,
                            'ADMIN': admin
                          })


@login_required(login_url=settings.LOGIN_URI)
def fdetemps(request):
    semaines = [0, 1]
    jours = {
        0: {'nom': "Dimanche", 'semaines': semaines},
        1: {'nom': "Lundi", 'semaines': semaines},
        2: {'nom': "Mardi", 'semaines': semaines},
        3: {'nom': "Mercredi", 'semaines': semaines},
        4: {'nom': "Jeudi", 'semaines': semaines},
        5: {'nom': "Vendredi", 'semaines': semaines},
        6: {'nom': "Samedi", 'semaines': semaines},
        }
    img = ImageReader('media/Feuilledetemps2.jpg')
    x = 5
    y = 5
    w = 600
    h = 750
    fichier = NOM_FICHIER_PDF
    #    doc = SimpleDocTemplate("/tmp/{}".format(NOM_FICHIER_PDF))
    if request.method == 'POST':
        y_sign = 615
        xjour = [
            [113, 138, 163, 188, 213, 238, 263],
            [299, 324, 348, 372, 396, 420, 445]
        ]
        y_heures = 418
        y_dates = 440
        somme_temps = 0

        date1 = request.POST.get('date')
        contratid = request.POST.get('contratid')
        commentaire = request.POST.get('commentaire')
        if contratid == "":
            messages.add_message(request, messages.ERROR, "Vous devez choisir un numéro de contrat")
            return render(request, 'fdt.html', {'jours': jours})
        if date1 == "":
            messages.add_message(request, messages.ERROR, "Vous devez rentrer une date")
            return render(request, 'fdt.html', {'jours': jours})

        detailcontrat = Contratippm.objects.get(pk=contratid)
        jour, mois, an = date1.split('/')
        date_rentree = datetime.date(int(an), int(mois), int(jour))
        semaine = date_rentree.strftime("%U")
        # Week number of the year (Sunday as the first day of the week) as a zero padded decimal number.
        # All days in a new year preceding the first Sunday are considered to be in week 0.
        debut = None
        if int(semaine) > 0:
            # les periodes de 2019 commencent les semaines paires
            if int(semaine) % 2 > 0:            # si num semaine impair
                d = str(an) + "-U" + semaine
                debut = datetime.datetime.strptime(d + '-0', "%Y-U%U-%w")
            else:
                semcorr = int(semaine) - 1
                d = str(an) + "-U" + str(semcorr)
                debut = datetime.datetime.strptime(d + '-0', "%Y-U%U-%w")

            fin = debut + datetime.timedelta(days=13)
            semaine_debut = debut.strftime("%U")
            quinzaine = (int(semaine_debut) + 4) / 2
        else:
            messages.add_message(request, messages.ERROR, "Il manque des informations, recommencez")
            return render(request, 'fdt.html', {'jours': jours})

        ddate = str(detailcontrat.datefin)
        an1, mois1, jour1 = ddate.split('-')
        datefin = datetime.datetime(int(an1), int(mois1), int(jour1))
        if datefin < debut:
            messages.add_message(request, messages.ERROR,
                                 "Le contrat est terminé: " + detailcontrat.datefin.strftime('%d/%m/%Y'))
            return render(request, 'fdt.html', {'jours': jours})

        if int(semaine_debut) % 2 > 0:  # si num semaine impair (devrait toujours etre ca)
            quinzaine = int(quinzaine + 1)
        else:
            quinzaine = int(quinzaine)

        date_debut = debut.strftime("%d-%m-%Y")
        date_fin = fin.strftime("%d-%m-%Y")
        data = request.user.last_name
        normal = unicodedata.normalize('NFD', data).encode('ascii', 'ignore').decode()

        nom_fichier = "{}{}_{}.pdf".format(fichier, normal, quinzaine)
        doc = Canvas("/tmp/{}".format(nom_fichier), pagesize=letter)
        doc.drawImage(img, x, y, w, h)
        doc.setFont('Helvetica', 10)
        doc.drawString(10, 10, PAGE_INFO)
        doc.drawString(330, y_sign, request.user.employe.numeemploye)
        doc.setFont('Helvetica', 12)
        doc.drawString(70, 750, 'No contrat : ' + detailcontrat.numcontrat)
#        doc.drawString(290, 750, 'No budget : ' + request.user.contratippm.numbudget)

        if request.user.employe.signature:
            signature = ImageReader(request.user.employe.signature)
            doc.drawImage(signature, 130, (y_sign - 15), 130, 50, mask='auto')

        doc.drawString(70, 636, request.user.first_name.capitalize() + " " + request.user.last_name.capitalize())

        doc.drawString(450, 645, 'PAIE : ' + str(quinzaine))
        doc.drawString(420, y_sign, date_debut)
        doc.drawString(515, y_sign, date_fin)
        doc.drawString(515, 115, date_fin)

        for semaine in semaines:
            temps_semaine = 0
            for jour in range(7):
                x = xjour[semaine][jour]
                val = request.POST.get("{}_{}".format(semaine, jour))
                doc.drawString(x, y_heures, val)
                somme_temps += float(val)
                temps_semaine += float(val)
                if semaine == 1:
                    ecart = jour + 7
                else:
                    ecart = jour
                newdate = debut + datetime.timedelta(days=ecart)
                doc.drawString(x, y_dates, newdate.strftime("%d"))
                if temps_semaine > float(detailcontrat.maxheures):
                    messages.add_message(request, messages.ERROR,
                                         "Nombre maximum d'heures autorisées par semaine : " + detailcontrat.maxheures)
                    return render(request, 'fdt.html', {'jours': jours})

        doc.drawString(515, y_heures, str(somme_temps))

        textobject = doc.beginText(60, 160)
        wraped_text = "\n".join(wrap(commentaire, 90))  # 80 is line width
        for line in wraped_text.splitlines(False):
            textobject.textLine(line.rstrip())
        doc.drawText(textobject)

        Tempsfacture.objects.update_or_create(user=request.user, periode=quinzaine,
                                              defaults={'heures': somme_temps, 'contrat': detailcontrat, 'commentaire': commentaire}
                                              )
        doc.save()
        fs = FileSystemStorage("/tmp")
        with fs.open(nom_fichier) as pdf:
            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="{}"'.format(nom_fichier)
        return response
    else:
        return render(request, 'fdt.html', {'jours': jours})
