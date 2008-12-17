# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.forms.models import inlineformset_factory 
from django.http import HttpResponse, Http404
from django.views.generic.list_detail import object_list, object_detail
from django.views.generic.create_update import create_object, delete_object, \
    update_object, get_model_and_form_class
from mimetypes import guess_type
from myapp.forms import FileForm
from myapp.models import Person, Contract, File
from ragendja.dbutils import get_object_or_404
from ragendja.forms import FormWithSets
from ragendja.template import render_to_response, render_to_string

def list_people(request):
    return object_list(request, Person.all(), paginate_by=10)

def show_person(request, key):
    return object_detail(request, Person.all(), key)

def add_person(request):
    return create_object(request, Person,
        post_save_redirect=reverse('myapp.views.show_person',
                                   kwargs=dict(key='%(key)s')))

def edit_person(request, key):
    model, form = get_model_and_form_class(Person, None)
    file_formset = inlineformset_factory(model, File, form=FileForm,
        exclude='content_type')
    employer_formset = inlineformset_factory(model, Contract,
        fk_name='employee')
    employee_formset = inlineformset_factory(model, Contract,
        fk_name='employer')
    form = FormWithSets(form, (('Files',{'formset':file_formset}),
        ('Employers',{'formset':employer_formset}),
        ('Employees',{'formset':employee_formset})))
    return update_object(request, model, key,  form_class=form,
        extra_context={'as':request.GET.get('as')})

def delete_person(request, key):
    return delete_object(request, Person, object_id=key,
        post_delete_redirect=reverse('myapp.views.list_people'))

def download_file(request, key, name):
    file = get_object_or_404(File, key)
    if file.name != name:
        raise Http404('Could not find file with this name!')
    return HttpResponse(file.file, content_type=guess_type(file.name))
