# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.forms.models import inlineformset_factory 
from django.http import HttpResponse, Http404
from django.views.generic.list_detail import object_list, object_detail
from django.views.generic.create_update import create_object, delete_object, \
    update_object, get_model_and_form_class
from mimetypes import guess_type
from myapp.forms import PersonForm
from myapp.models import Person, Contract, File
from ragendja.dbutils import get_object_or_404

def list_people(request):
    return object_list(request, Person.all(), paginate_by=10)

def show_person(request, key):
    return object_detail(request, Person.all(), key)

def add_person(request):
    return create_object(request, Person,
        post_save_redirect=reverse('myapp.views.show_person',
                                   kwargs=dict(key='%(key)s')))

def edit_person(request, key):
    return update_object(request, object_id=key, form_class=PersonForm,
        extra_context={'as':request.GET.get('as')})

def delete_person(request, key):
    return delete_object(request, Person, object_id=key,
        post_delete_redirect=reverse('myapp.views.list_people'))

def download_file(request, key, name):
    file = get_object_or_404(File, key)
    if file.name != name:
        raise Http404('Could not find file with this name!')
    return HttpResponse(file.file, content_type=guess_type(file.name))
