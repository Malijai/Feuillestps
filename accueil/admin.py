from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Employe, Contratippm, Role, Tempsfacture, Secretaire, Periodes


class PeriodesAdmin(admin.ModelAdmin):
    model = Periodes
    can_delete = False


class SecretaireAdmin(admin.ModelAdmin):
    model = Secretaire
    can_delete = False


class TempsInline(admin.StackedInline):
    model = Contratippm
    can_delete = False


class AddInline(admin.StackedInline):
    model = Employe
    can_delete = False


class RolelInline(admin.StackedInline):
    model = Role
    can_delete = False
    extra = 1
    min_num = 1


class UserRoleAdmin(UserAdmin):
    inlines = (RolelInline,)
    list_display = ('username', 'email','first_name', 'last_name', 'is_active', 'last_login')
    list_filter = ('is_active',)

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super(UserRoleAdmin, self).get_inline_instances(request,obj)


class TempsUserAdmin(UserAdmin):
    inlines = (RolelInline, TempsInline, AddInline)
    list_display = ('username', 'email','first_name', 'last_name', 'is_active', 'last_login')
    list_filter = ('is_active',)

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super(TempsUserAdmin, self).get_inline_instances(request,obj)


class TempsfactureAdmin(admin.ModelAdmin):
    model = Tempsfacture
    can_delete = False
    list_display = ('user', 'contrat', 'periode', 'brutperiode', 'partemployeur', 'partemployeurcorr')


admin.site.unregister(User)
admin.site.register(User, UserRoleAdmin)
admin.site.register(Tempsfacture, TempsfactureAdmin)
admin.site.register(Secretaire, SecretaireAdmin)
admin.site.register(Periodes, PeriodesAdmin)
