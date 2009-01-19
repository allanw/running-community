from django.contrib import admin
from myapp.models import Person, File

class FileInline(admin.TabularInline):
    model = File

class PersonAdmin(admin.ModelAdmin):
    inlines = (FileInline,)

admin.site.register(Person, PersonAdmin)
