from django.db import models
from django.contrib.auth.models import User


class Employe(models.Model):
    user = models.OneToOneField(User, on_delete=models.DO_NOTHING)
    numeemploye = models.CharField(max_length=100, verbose_name="Numero d'employé IPPM", unique=True, null=True, blank=True)
    signature = models.ImageField(upload_to='signatures', verbose_name="Signature au format jpeg", help_text="PAS D'ACCENT DANS LES NOMS DE FICHIERS", null=True, blank=True)

    def __str__(self):
        return '%s' % self.numeemploye


class Projet(models.Model):
    nomcourt = models.CharField(max_length=15, verbose_name="Nom abrégé du projet", unique=True,null=True, blank=True)
    nomlong = models.CharField(max_length=250, verbose_name="Nom complet du projet", unique=True, null=True, blank=True)
    budget = models.CharField(max_length=20, verbose_name="Numéro du budget INPLPP", null=True, blank=True)
    origine = models.CharField(max_length=250, verbose_name="Origine des fonds", null=True, blank=True)
    responsable = models.CharField(max_length=100, verbose_name="Responsable du projet", null=True, blank=True)

    def __str__(self):
        return '%s' % self.nomcourt


class Niveau(models.Model):
    reponse = models.CharField(max_length=256, verbose_name="Niveau scolaire/universitaire", default=1)

    def __str__(self):
        return '%s' % self.reponse


class Contratippm(models.Model):
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    numcontrat = models.CharField(max_length=30, verbose_name="Numero Contrat", unique=True, null=True, blank=True)
    maxheures = models.CharField(max_length=30, verbose_name="Nb maximum d'heures par semaine", null=True, blank=True)
    datedebut = models.DateField(verbose_name="Date du debut du contrat")
    datefin = models.DateField(verbose_name="Date de fin du contrat")
    tauxhoraire = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Taux horaire pour ce contrat")
    niveau = models.ForeignKey(Niveau, verbose_name="Niveau scolaire/universitaire", on_delete=models.DO_NOTHING)
    projet = models.ForeignKey('Projet', verbose_name="Projet", on_delete=models.DO_NOTHING)
    vacancesexclues = models.BooleanField(default='False')
    role = models.CharField(max_length=50, verbose_name="Rôle / statut", null=True, blank=True)

    def __str__(self):
        return '{0} - {1}'.format(self.numcontrat, self.nomprojet)



class Periodes(models.Model):
    periode = models.IntegerField(verbose_name="Numéro de la période")
    anneefiscale = models.CharField(max_length=30, verbose_name="Année fiscale")
    datedebut = models.DateField(default="2000-01-01")
    datefin = models.DateField(default="2000-01-01")


class Tempsfacture(models.Model):
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    periode = models.IntegerField(verbose_name="Numero de la periode", null=True, blank=True)
    bonneperiode = models.ForeignKey(Periodes, on_delete=models.DO_NOTHING)
    heures = models.CharField(max_length=30, verbose_name="Nb d'heures facturées dans la période", null=True, blank=True)
    contrat = models.ForeignKey(Contratippm, on_delete=models.DO_NOTHING)
    commentaire = models.CharField(max_length=250, null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    debutperiode = models.DateField(default="2000-01-01")
    partemployeur = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Part de l employeur")
    brutperiode = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Salaire brut")
    partemployeurcorr = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name="Correction part employeur")
    correction = models.IntegerField(default=0)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['user', 'bonneperiode']

    def __str__(self):
        return '%s' % self.user


class Role(models.Model):
    RA = 1
    ADMIN = 2
    ROLES_CHOICES = (
        (RA, 'Assistants de recherche'),
        (ADMIN, 'Administrateur'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.PositiveSmallIntegerField(choices=ROLES_CHOICES, verbose_name="Roles", default=1)
    # mettre RA par defaut

    def __str__(self):
        return '{0} - {1}'.format(self.user.last_name, self.user.first_name)


class Charges(models.Model):
    rrqtaux = models.DecimalField(max_digits=5, decimal_places=3, verbose_name="Taux RRQ (%)")
    rrqexemption = models.IntegerField(verbose_name="Exemption RRQ")
    rrqmax = models.IntegerField(verbose_name="RRQ : salaire cotisable maximal")
    cnesttaux = models.DecimalField(max_digits=5, decimal_places=3, verbose_name="Taux CNEST (%)")
    fssttaux = models.DecimalField(max_digits=5, decimal_places=3, verbose_name="Taux FSS (%)")
    assemploitaux = models.DecimalField(max_digits=5, decimal_places=3, verbose_name="Assurance emploi taux plein")
    assemploimax = models.IntegerField(verbose_name="Assurance emploi : salaire cotisable maximal")
    rqaptaux = models.DecimalField(max_digits=5, decimal_places=3, verbose_name="Taux RQAP (%)")
    rqapmax = models.IntegerField(verbose_name="RQAP : salaire cotisable maximal")
    datedebut = models.DateField(default="2000-01-01")
    datefin = models.DateField(default="2000-01-01")
