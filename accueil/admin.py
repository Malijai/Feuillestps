from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Employe, Contratippm, Role


class TempsInline(admin.StackedInline):
    model = Contratippm
    can_delete = False


class AddInline(admin.StackedInline):
    model = Employe
    can_delete = False


class RolelInline(admin.StackedInline):
    model = Role
    can_delete = False


class TempsUserAdmin(UserAdmin):
    inlines = (RolelInline, TempsInline, AddInline)
    list_display = ('username', 'email','first_name', 'last_name', 'is_active', 'last_login')
    list_filter = ('is_active',)

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super(TempsUserAdmin, self).get_inline_instances(request,obj)


admin.site.unregister(User)
admin.site.register(User, TempsUserAdmin)