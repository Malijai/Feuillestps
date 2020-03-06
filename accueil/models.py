from django.db import models
from django.contrib.auth.models import User


class Employe(models.Model):
    user = models.OneToOneField(User, on_delete=models.DO_NOTHING)
    numeemploye = models.CharField(max_length=256, verbose_name="Numero d'employé IPPM", null=True, blank=True)
    signature = models.ImageField(upload_to='signatures', verbose_name="Signature au format jpeg", help_text="PAS D'ACCENT DANS LES NOMS DE FICHIERS", null=True, blank=True)

    def __str__(self):
        return '%s' % self.numeemploye


class Contratippm(models.Model):
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    numcontrat = models.CharField(max_length=30, verbose_name="Numero Contrat", null=True, blank=True)
    numbudget = models.CharField(max_length=30, verbose_name="Numero Budget", null=True, blank=True)
    nomprojet = models.CharField(max_length=200, verbose_name="Nom abrégé du projet", null=True, blank=True)
    maxheures = models.CharField(max_length=30, verbose_name="Nb maximum d'heures par semaine", null=True, blank=True)
    datedebut = models.DateField(verbose_name="Date du debut du contrat")
    datefin = models.DateField(verbose_name="Date de fin du contrat")
    tauxhoraire = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Taux horaire pour ce contrat")

    def __str__(self):
        return '{0} - {1}'.format(self.numcontrat, self.nomprojet)


class Tempsfacture(models.Model):
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    periode = models.IntegerField(verbose_name="Numero de la periode")
    heures = models.CharField(max_length=30, verbose_name="Nb d'heures facturées dans la période", null=True, blank=True)
    contrat = models.ForeignKey(Contratippm, on_delete=models.DO_NOTHING)
    commentaire =  models.CharField(max_length=250, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    debutperiode = models.DateField(default="2000-01-01")

    class Meta:
        ordering = ['user', 'periode']

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
    role = models.PositiveSmallIntegerField(choices=ROLES_CHOICES, verbose_name="Roles", null=True, blank=True)

    # mettre RA par defaut

    def __str__(self):
        return self.user.username
