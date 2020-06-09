from __future__ import unicode_literals
from django.shortcuts import render, redirect
from django.conf import settings
from django.http import HttpResponse
from django.contrib import messages
from .models import Tempsfacture, Contratippm, Role, User, Employe, Projet, Periodes, Charges
from .forms import ContratFormSet, UserForm, EmployeForm, ProjetForm
from reportlab.pdfgen.canvas import Canvas
from django.core.files.storage import FileSystemStorage
from reportlab.lib.utils import ImageReader
from reportlab.lib.pagesizes import letter
from django.contrib.auth.decorators import login_required
import datetime
import unicodedata
from textwrap import wrap
from django.db.models import Q, Sum, Count
import decimal


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
    try:
        employe = Employe.objects.get(user=assistant)
    except Employe.DoesNotExist:
        employe = None
    if request.method == 'POST':
        assistant_form = UserForm(request.POST, instance=assistant)
        if employe is not None:
            employe_form = EmployeForm(request.POST, request.FILES, instance=employe)
        else:
            employe_form = EmployeForm(request.POST, request.FILES)
        if assistant_form.is_valid():
            assistant = assistant_form.save()
        if employe_form.is_valid():
            entree = employe_form.save(commit=False)
            entree.user = User.objects.get(pk=pk)
            entree.save()
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
        an, mois, jour = date1.split('-')
        date_rentree = datetime.date(int(an), int(mois), int(jour))
        semaine = date_rentree.strftime("%U")

        periode = Periodes.objects.get(Q(datedebut__lte=date_rentree) & Q(datefin__gte=date_rentree))
        print('periode ', periode.periode)
        debut = periode.datedebut
        fin = periode.datefin
        quinzaine = periode.periode

        ddate = str(detailcontrat.datefin)
        an1, mois1, jour1 = ddate.split('-')
        datefin = datetime.datetime(int(an1), int(mois1), int(jour1)).date()
        if datefin < debut:
            messages.add_message(request, messages.ERROR,
                                 "Le contrat est terminé: " + detailcontrat.datefin.strftime('%d/%m/%Y'))
            return render(request, 'fdt.html', {'jours': jours})

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
        doc.drawString(50, 750, 'No contrat : ' + detailcontrat.numcontrat)
        doc.drawString(250, 750, 'No budget : ' + detailcontrat.projet.budget)
        doc.drawString(400, 750, 'Statut : ' + detailcontrat.role)

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
        # Calculs pour enregistrement des donnees dans la BD
        debutperiode = debut.strftime("%Y-%m-%d")
        brutperiode, partemployeur = calcul_salaire(detailcontrat.tauxhoraire, somme_temps, debutperiode)
        # Enregistrement des donnees dans la BD
        Tempsfacture.objects.update_or_create(user=request.user, bonneperiode=periode,
                                              defaults={'heures': somme_temps,
                                                        'contrat': detailcontrat,
                                                        'commentaire': commentaire,
                                                        'partemployeur': partemployeur,
                                                        'brutperiode': brutperiode,
                                                        }
                                              )
        doc.save()
        fs = FileSystemStorage("/tmp")
        with fs.open(nom_fichier) as pdf:
            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="{}"'.format(nom_fichier)
        return response
    else:
        return render(request, 'fdt.html', {'jours': jours})


def calcul_salaire(tauxhoraire, somme_temps, debutperiode):
    brutperiode = decimal.Decimal(somme_temps) * tauxhoraire
    charge = Charges.objects.get(Q(datedebut__lte=debutperiode) & Q(datefin__gte=debutperiode))
    taux_autres = charge.fssttaux + charge.assemploitaux + charge.rqaptaux + charge.cnesttaux
    partemployeur1 = decimal.Decimal(brutperiode * (taux_autres /100))
    exemptionrrq = decimal.Decimal(charge.rrqexemption / 27)
    if brutperiode > exemptionrrq:
        partemployeur2 = decimal.Decimal(brutperiode - exemptionrrq) * decimal.Decimal(charge.rrqtaux /100)
    else:
        partemployeur2 = 0
    partemployeur = partemployeur1 + partemployeur2
    return brutperiode, partemployeur


@login_required(login_url=settings.LOGIN_URI)
def bilanparcontrat(request, pk, cid):
    assistant = User.objects.get(pk=pk)
    contrat = Contratippm.objects.get(pk=cid)
    temps = Tempsfacture.objects.filter(user=assistant, contrat=contrat).order_by('bonneperiode__datedebut')
    vacances = 0
    totalbrut = 0
    totalcharges = 0
    totalheures = 0
    if temps:
        tempscontrat1 = Tempsfacture.objects.filter(Q(correction=0) & Q(user=assistant) & Q(contrat=contrat))\
            .aggregate(Sum('heures'), Sum('brutperiode'), Sum('partemployeur'))
        tempscontrat2 = Tempsfacture.objects.filter(Q(correction=1) & Q(user=assistant) & Q(contrat=contrat)) \
            .aggregate(Sum('heures'), Sum('brutperiode'), Sum('partemployeurcorr'))
        if tempscontrat2['brutperiode__sum'] is not None:
            totalbrut = tempscontrat1['brutperiode__sum'] + tempscontrat2['brutperiode__sum']
            totalcharges = tempscontrat1['partemployeur__sum'] + tempscontrat2['partemployeurcorr__sum']
            totalheures = tempscontrat1['heures__sum'] + tempscontrat2['heures__sum']
        else:
            totalbrut = tempscontrat1['brutperiode__sum']
            totalcharges = tempscontrat1['partemployeur__sum']
            totalheures = tempscontrat1['heures__sum']

        vacances = totalbrut * decimal.Decimal('0.04')

    return render(request, "bilan.html", {'RA': assistant,
                                          'contrat': contrat,
                                          'temps': temps,
                                          'vacances': vacances,
                                          'totalbrut': totalbrut,
                                          'totalcharges': totalcharges,
                                          'totalheures': totalheures})


@login_required(login_url=settings.LOGIN_URI)
def listecontrats(request):
    contrats = Contratippm.objects.all().order_by('datedebut')
    assistants = Role.objects.filter(role=1).order_by('user__last_name')
    return render(request, 'listecontrats.html', {'RAs': assistants, 'contrats': contrats})


@login_required(login_url=settings.LOGIN_URI)
def bilanparprojet(request):
    contrats = Contratippm.objects.values('nomprojet').annotate(Count('numcontrat'))
    print(contrats)
    assistants = Role.objects.filter(role=1).order_by('user__last_name')
    return render(request, 'liste.html', {'RAs': assistants})


@login_required(login_url=settings.LOGIN_URI)
def projet_new(request):
    if request.method == "POST":
        form = ProjetForm(request.POST)
        if form.is_valid():
            projet = form.save(commit=False)
            projet.save()
            messages.success(request, "Le projet a été ajouté à la liste")
            return redirect('listeprojets')
        else:
            messages.error(request, "Il y a eu une erreur dans la création du projet, recommencez")
    else:
        form = ProjetForm()
    return render(request, 'projet_edit.html', {'form': form})


@login_required(login_url=settings.LOGIN_URI)
def listeprojets(request):
    projets = Projet.objects.all().order_by('nomcourt')
    return render(request, 'projet_liste.html', {'projets': projets})


def mise_a_jour_db(request, pk):
    temppsassistant = Tempsfacture.objects.filter(Q(user_id=pk) & Q(debutperiode__gte='2020-03-01'))
    for tps in temppsassistant:
        taux = tps.contrat.tauxhoraire
        brutperiode, partemployeur = calcul_salaire(taux, tps.heures)
        Tempsfacture.objects.update_or_create(id=tps.id,
                                          defaults={'partemployeur': partemployeur,
                                                    'brutperiode': brutperiode
                                                    }
                                          )
    return redirect('listeassistants')
