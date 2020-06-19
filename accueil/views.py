from __future__ import unicode_literals
from django.shortcuts import render, redirect
from django.conf import settings
from django.http import HttpResponse
from django.contrib import messages
from .models import Tempsfacture, Contratippm, Role, User, Employe, Projet, Periodes, Charges, Niveau, Secretaire
from .forms import ContratFormSet, UserForm, EmployeForm, ProjetForm, TempsForm, EvaluationForm
from reportlab.pdfgen.canvas import Canvas
from django.core.files.storage import FileSystemStorage
from reportlab.lib.utils import ImageReader
from reportlab.lib.pagesizes import letter
from django.contrib.auth.decorators import login_required
import datetime
from datetime import timedelta
import unicodedata
from textwrap import wrap
from django.db.models import Q, Sum, Count
import decimal
from collections import OrderedDict


NOM_FICHIER_PDF = "FeuilleTemps_"
PAGE_INFO = "Feuilles de temps - Date d'impression : " + datetime.datetime.now().strftime('%d/%m/%Y')

DATE = datetime.datetime.now().strftime('%Y %b %d')


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
    secretaire =  Secretaire.objects.get(actif=True)
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
            return render(request, 'fdt.html', {'jours': jours, 'secretaire': secretaire})
        if date1 == "":
            messages.add_message(request, messages.ERROR, "Vous devez rentrer une date")
            return render(request, 'fdt.html', {'jours': jours, 'secretaire': secretaire})

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
            return render(request, 'fdt.html', {'jours': jours, 'secretaire': secretaire})

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
                    return render(request, 'fdt.html', {'jours': jours, 'secretaire': secretaire})
        doc.drawString(515, y_heures, str(somme_temps))
        textobject = doc.beginText(60, 160)
        wraped_text = "\n".join(wrap(commentaire, 90))  # 90 is line width
        for line in wraped_text.splitlines(False):
            textobject.textLine(line.rstrip())
        doc.drawText(textobject)
        # Calculs pour enregistrement des donnees dans la BD
        debutperiode = debut.strftime("%Y-%m-%d")
        brutperiode, partemployeur, vacances = calcul_salaire(detailcontrat.tauxhoraire, somme_temps, debutperiode, detailcontrat.vacancestaux)
        # Enregistrement des donnees dans la BD
        Tempsfacture.objects.update_or_create(user=request.user, bonneperiode=periode,
                                              defaults={'heures': somme_temps,
                                                        'contrat': detailcontrat,
                                                        'commentaire': commentaire,
                                                        'partemployeur': partemployeur,
                                                        'brutperiode': brutperiode,
                                                        'vacances': vacances,
                                                        }
                                              )
        doc.save()
        fs = FileSystemStorage("/tmp")
        with fs.open(nom_fichier) as pdf:
            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="{}"'.format(nom_fichier)
        return response
    else:
        return render(request, 'fdt.html', {'jours': jours, 'secretaire': secretaire})


def calcul_salaire(tauxhoraire, somme_temps, debutperiode, tauxvacances):
    brutperiode = decimal.Decimal(somme_temps) * decimal.Decimal(tauxhoraire)
    charge = Charges.objects.get(Q(datedebut__lte=debutperiode) & Q(datefin__gte=debutperiode))
    taux_autres = charge.fssttaux + charge.assemploitaux + charge.rqaptaux + charge.cnesttaux
    partemployeur1 = decimal.Decimal(brutperiode * (taux_autres /100))
    exemptionrrq = decimal.Decimal(charge.rrqexemption / 27)
    if brutperiode > exemptionrrq:
        partemployeur2 = decimal.Decimal(brutperiode - exemptionrrq) * decimal.Decimal(charge.rrqtaux /100)
    else:
        partemployeur2 = 0
    vacances = decimal.Decimal(brutperiode) * decimal.Decimal(decimal.Decimal(tauxvacances) /100)
    partemployeur = partemployeur1 + partemployeur2
    return brutperiode, partemployeur, vacances


@login_required(login_url=settings.LOGIN_URI)
def bilanparcontrat(request, cid):
    contrat = Contratippm.objects.get(pk=cid)
    temps = Tempsfacture.objects.filter(contrat=contrat).order_by('bonneperiode__datedebut')
    if temps:
        touteslesannees = []
        tempscontrat0 = Tempsfacture.objects.filter(Q(correction=0) & Q(contrat=contrat))\
            .aggregate(h0=Sum('heures'), b0=Sum('brutperiode'), pe0=Sum('partemployeur'), v0=Sum('vacances'))
        tempscontrat1 = Tempsfacture.objects.filter(Q(correction=1) & Q(contrat=contrat)) \
            .aggregate(h1=Sum('heures'), b1=Sum('brutperiode'), pe1=Sum('partemployeurcorr'), v1=Sum('vacances'))
        totalheures, totalbrut, totalcharges, totalvacances = fait_totaux(tempscontrat0, tempscontrat1)

        anneesfiscales = Tempsfacture.objects.values('bonneperiode__anneefiscale').filter(Q(contrat=contrat))\
                        .distinct()
        for annee in anneesfiscales:
            ligneannee = []
            anneef = annee['bonneperiode__anneefiscale']

            anneefiscale0 = Tempsfacture.objects.values('bonneperiode__anneefiscale').filter(Q(correction=0) & Q(contrat=contrat) & Q(bonneperiode__anneefiscale=anneef)) \
                    .aggregate(h0=Sum('heures'), b0=Sum('brutperiode'), pe0=Sum('partemployeur'), v0=Sum('vacances'))
            anneefiscale1 = Tempsfacture.objects.values('bonneperiode__anneefiscale').filter(Q(correction=1) & Q(contrat=contrat) & Q(bonneperiode__anneefiscale=anneef)) \
                    .aggregate(h1=Sum('heures'), b1=Sum('brutperiode'), pe1=Sum('partemployeurcorr'), v1=Sum('vacances'))

            totalheuresa, totalbruta, totalchargesa, totalvacancesa = fait_totaux(anneefiscale0, anneefiscale1)
            ligneannee.append(anneef)
            ligneannee.append(totalheuresa)
            ligneannee.append(totalbruta)
            ligneannee.append(totalchargesa)
            ligneannee.append(totalvacancesa)
            touteslesannees.append(ligneannee)

        return render(request, "bilanpcontrat.html", {'contrat': contrat,
                                          'temps': temps,
                                          'vacances': totalvacances,
                                          'totalbrut': totalbrut,
                                          'totalcharges': totalcharges,
                                          'totalheures': totalheures,
                                          'touteslesannees': touteslesannees})
    else:
        messages.error(request, "Il n'y a pas eu d'heures facturées pour ce contrat.")
        return render(request, "bilanpcontrat.html", {'contrat': contrat,})


def fait_totaux(noncorrigee, corrigee):
    totalheuresa = noncorrigee['h0']
    totalbruta = noncorrigee['b0']
    totalchargesa = noncorrigee['pe0']
    totalvacances = noncorrigee['v0']
    if totalheuresa is None:
        totalheuresa = 0
        totalbruta = 0
        totalchargesa = 0
        totalvacances = 0
    if corrigee['h1'] is not None:
        totalheuresa = totalheuresa + corrigee['h1']
        totalbruta = totalbruta + corrigee['b1']
        totalchargesa = totalchargesa + corrigee['pe1']
        totalvacances = totalvacances + corrigee['v1']
    return totalheuresa,totalbruta, totalchargesa, totalvacances


@login_required(login_url=settings.LOGIN_URI)
def listecontrats(request):
    contrats = Contratippm.objects.all().order_by('datedebut')
    assistants = Role.objects.filter(role=1).order_by('user__last_name')
    return render(request, 'listecontrats.html', {'RAs': assistants, 'contrats': contrats})


@login_required(login_url=settings.LOGIN_URI)
def bilanparprojet(request, pid):
    contrats = Contratippm.objects.filter(projet=pid).order_by('user__last_name', 'datedebut')
    projet = Projet.objects.get(pk=pid)
    tempstous = []
    for contrat in contrats:
        temps = Tempsfacture.objects.filter(contrat=contrat).order_by('user','bonneperiode__datedebut')
        tempstous.extend(temps)
    anneesfiscales = Tempsfacture.objects.values('bonneperiode__anneefiscale').filter(contrat__in = contrats).distinct()
    touteslesannees = []
    comparaison = set([])
    touslesniveaux = []
    niveaux = set()
    for annee in anneesfiscales:
        ligneannee = []
        contrats_ar = Tempsfacture.objects.values('contrat__niveau','contrat','contrat__numcontrat', 'user','user__last_name', 'contrat__niveau__reponse')\
            .filter(Q(bonneperiode__anneefiscale=annee['bonneperiode__anneefiscale']) & Q(contrat__in=contrats))\
            .order_by('user__last_name','contrat__numcontrat')
        liste_c_ras = []
        for c_ra in contrats_ar:
            liste_c_ras.append(c_ra['user'])
            liste_c_ras.append(c_ra['contrat'])
            value = tuple([c_ra['user'], c_ra['user__last_name'],c_ra['contrat'], c_ra['contrat__numcontrat'], annee['bonneperiode__anneefiscale'], c_ra['contrat__niveau__reponse']])
            comparaison.add(value)
            niv = (c_ra['contrat__niveau'])
            niveaux.add(niv)
        for niveau in niveaux:
            ligneniveau = []
            anneef = annee['bonneperiode__anneefiscale']
            anneefiscale0 = Tempsfacture.objects.values('bonneperiode__anneefiscale').filter(
                Q(correction=0) & Q(contrat__in=contrats) & Q(contrat__niveau=niveau) & Q(bonneperiode__anneefiscale=anneef)) \
                .aggregate(h0=Sum('heures'), b0=Sum('brutperiode'), pe0=Sum('partemployeur'), v0=Sum('vacances'))
            anneefiscale1 = Tempsfacture.objects.values('bonneperiode__anneefiscale').filter(
                Q(correction=1) & Q(contrat__in=contrats) & Q(contrat__niveau=niveau)  & Q(bonneperiode__anneefiscale=anneef)) \
                .aggregate(h1=Sum('heures'), b1=Sum('brutperiode'), pe1=Sum('partemployeurcorr'), v1=Sum('vacances'))
            totalheuresa, totalbruta, totalchargesa, totalvacances = fait_totaux(anneefiscale0, anneefiscale1)
            niveau_nom = Niveau.objects.get(pk=niveau)
            ligneniveau.append(anneef)
            ligneniveau.append(totalheuresa)
            ligneniveau.append(totalbruta)
            ligneniveau.append(totalchargesa)
            ligneniveau.append(totalvacances)
            ligneniveau.append(niveau_nom.reponse)
            touslesniveaux.append(ligneniveau)

        anneef = annee['bonneperiode__anneefiscale']
        anneefiscale0 = Tempsfacture.objects.values('bonneperiode__anneefiscale').filter(
                Q(correction=0) & Q(contrat__in = contrats) & Q(bonneperiode__anneefiscale=anneef)) \
                .aggregate(h0=Sum('heures'), b0=Sum('brutperiode'), pe0=Sum('partemployeur'), v0=Sum('vacances'))
        anneefiscale1 = Tempsfacture.objects.values('bonneperiode__anneefiscale').filter(
                Q(correction=1) & Q(contrat__in = contrats) & Q(bonneperiode__anneefiscale=anneef)) \
                .aggregate(h1=Sum('heures'), b1=Sum('brutperiode'), pe1=Sum('partemployeurcorr'), v1=Sum('vacances'))
        totalheuresa, totalbruta, totalchargesa, totalvacances = fait_totaux(anneefiscale0, anneefiscale1)
        ligneannee.append(anneef)
        ligneannee.append(totalheuresa)
        ligneannee.append(totalbruta)
        ligneannee.append(totalchargesa)
        ligneannee.append(totalvacances)
        touteslesannees.append(ligneannee)

    return render(request, 'bilanpprojet.html', {'contrats': contrats,
                                                 'temps': tempstous,
                                                 'touteslesannees': touteslesannees,
                                                 'touslesniveaux': touslesniveaux,
                                                 'lignes': comparaison,
                                                 'projet': projet})


@login_required(login_url=settings.LOGIN_URI)
def listeprojets(request):
    projets = Projet.objects.all().order_by('nomcourt')
    return render(request, 'projet_liste.html', {'projets': projets})


def correction_pe(request, pk):
    tps = Tempsfacture.objects.get(pk=pk)
    if request.method == 'POST':
        tps_form = TempsForm(request.POST, instance=tps)
        if tps_form.is_valid():
            tpscorr = tps_form.save(commit=False)
            tpscorr.correction = 1
            tpscorr.save()
            messages.success(request, "La part de l'employeur a été corrigée.")
            return redirect(bilanparcontrat, tps.contrat.id)
    else:
        tps_form = TempsForm(instance=tps)
    return render(request, 'tempsperiode_edit.html', {'form': tps_form, 'temps': tps})


def mise_a_jour_db(request, pk):
    contrats = Contratippm.objects.filter(projet=pk)
    for contrat in contrats:
        temps = Tempsfacture.objects.filter(contrat=contrat)
        for tps in temps:
            brutperiode = 0
            partemployeur = 0
            vacances = 0
            taux = tps.contrat.tauxhoraire
            brutperiode, partemployeur, vacances = calcul_salaire(taux, tps.heures, tps.debutperiode, tps.contrat.vacancestaux)

            Tempsfacture.objects.update_or_create(id=tps.id,
                                            defaults={'partemployeur': partemployeur,
                                                       'brutperiode': brutperiode,
                                                       'vacances': vacances
                                                    }
                                          )
    return redirect('listeassistants')


def calcule_couts(request):
    form_class = EvaluationForm
    nbsemaines = 0
    bruth = 0
    partemployeurh = 0
    vacancesh = 0
    totalbrut = 0
    totalpartemployeur = 0
    totalvacances = 0
    datedebut = ''
    datefin = ''
    heuressemaine = ''
    tauxhoraire = ''
    tauxvacances = ''
    if request.method == 'POST':
        datedebut = request.POST.get('datedebut')
        datefin = request.POST.get('datefin')
        heuressemaine = request.POST.get('heuressemaine')
        tauxhoraire = request.POST.get('tauxhoraire')
        tauxvacances = request.POST.get('tauxvacances')
        jourdeb, moisdeb, andeb = datedebut.split('-')
        semainedeb_rentree = datetime.date(int(andeb), int(moisdeb), int(jourdeb))
        jourfin, moisfin, anfin = datefin.split('-')
        semainefin_rentree = datetime.date(int(anfin), int(moisfin), int(jourfin))
        monday1 = (semainedeb_rentree - timedelta(days=semainedeb_rentree.weekday()))
        monday2 = (semainefin_rentree - timedelta(days=semainefin_rentree.weekday()))
        nbsemaines = (monday2 - monday1).days / 7
        bruth, partemployeurh, vacancesh = calcul_salaire(decimal.Decimal(tauxhoraire),
                                                          decimal.Decimal(heuressemaine),
                                                          semainedeb_rentree,
                                                          decimal.Decimal(tauxvacances))
        totalbrut = bruth * decimal.Decimal(nbsemaines)
        totalpartemployeur = partemployeurh * decimal.Decimal(nbsemaines)
        totalvacances = decimal.Decimal(vacancesh) * decimal.Decimal(nbsemaines)
        grandtotal = totalvacances + totalpartemployeur + totalbrut
    else:
        form_class = EvaluationForm()

    return render(request, 'evaluation_cout.html', {'form': form_class,
                                                    'datedebut': datedebut,
                                                    'datefin': datefin,
                                                    'heuressemaine': heuressemaine,
                                                    'tauxhoraire': tauxhoraire,
                                                    'tauxvacances': tauxvacances,
                                                    'nbsemaines': nbsemaines,
                                                    'bruth': bruth,
                                                    'partemployeurh': partemployeurh,
                                                    'vacancesh': vacancesh,
                                                    'totalbrut': totalbrut,
                                                    'totalpartemployeur': totalpartemployeur,
                                                    'totalvacances': totalvacances,
                                                    'grandtotal': grandtotal,
                                                    })