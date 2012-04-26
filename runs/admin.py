from django.contrib import admin
from runs.models import Poll, Choice, NikePlusInfo, Run

class ChoiceInline(admin.TabularInline):
    fields = ['choice', 'votes']
    model = Choice
    extra = 3

class PollAdmin(admin.ModelAdmin):
    fieldsets = [
        (None,               {'fields': ['question']}),
        ('Date information', {'fields': ['pub_date'], 'classes': ['collapse']}),
    ]
    inlines = [ChoiceInline]

    list_display = ('question', 'pub_date', 'was_published_today')
    # N.B. filtering doesn't seem to work properly with appengine's db.DateTimeProperty
    # On the right of the change list page I do get a filter section, but none of the expected
    # options e.g. 'Any date', 'Today', 'Past 7 days', etc.
    list_filter = ['pub_date']

    # Searching in the change list page also doesn't seem to work
    search_fields = ['question']


admin.site.register(Poll, PollAdmin)
admin.site.register(NikePlusInfo)
admin.site.register(Run)
