from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms import model_to_dict
from django.http import HttpResponse, HttpResponseNotFound, Http404, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy, resolve
from django.template.loader import render_to_string
from django.template.defaultfilters import slugify
from django.utils.timezone import now
from django.views import View
from django.views.generic import ListView, DetailView, FormView, UpdateView
from cars.models import Mine, Shaft, Site, Plan_zadanie, Plotnost_gruza, Schema_otkatki, T_smeny, T_regl_pereryv, \
    T_pereezd, T_vspom, Nsmen, YearMonth, V_objem_kuzova, Kuzov_Coeff_Zapl, V_Skorost_dvizh, T_pogruzki,  T_razgruzki
from .forms import SiteEditForm, PlanZadanieFormset, Plotnost_gruzaFormset, Schema_otkatkiFormset, T_smenyFormset, \
    T_regl_pereryvFormset, T_pereezdFormset, T_vspomFormset, NsmenFormset, PropertyEditForm, UniversalPropertyForm
from itertools import chain
from django.apps import apps


from cars.forms import AddPostForm, UploadFilesForm, SiteEditForm, get_universal_property_form
from cars.models import Car, Category, TagPost, UploadFiles

import pandas as pd
from django.conf import settings
from .site_data_service import SiteDataService
from django.utils.html import format_html_join, mark_safe


class UniversalPropertyView(View):
    models = {
        'plan_zadanie': Plan_zadanie,
        'plotnost_gruza': Plotnost_gruza,
        'schema_otkatki': Schema_otkatki,
        't_smeny': T_smeny,
        't_regl_pereryv': T_regl_pereryv,
        't_pereezd': T_pereezd,
        't_vspom': T_vspom,
        'nsmen': Nsmen,
        'Vk': V_objem_kuzova,
        'Kz': Kuzov_Coeff_Zapl,
        'Vdv': V_Skorost_dvizh,
        'Tpogr': T_pogruzki,
        'Trazgr': T_razgruzki,
    }

    def get(self, request, property_type, *args, **kwargs):
        model_class = self.models.get(property_type)
        if not model_class:
            return redirect('error_page')  # handle the error appropriately
        else:
            site_slug = kwargs.get('site_slug')
            initial_site = get_object_or_404(Site, slug=site_slug)
            property_verbose_name = model_class._meta.verbose_name

            # Query the latest record for the property type
            latest_record = model_class.objects.filter(site=initial_site).order_by('-created').first()
            initial_data = model_to_dict(latest_record) if latest_record else None

            PropertyForm = get_universal_property_form(model_class, initial_site=initial_site, user=request.user, initial=initial_data)
            form = PropertyForm(initial=initial_data)  # instantiate the form class
            return render(request, 'universal_property_form.html', {
                'form': form,
                'property_verbose_name': property_verbose_name,
                'site_slug':site_slug,
                'site': initial_site})


    def post(self, request, property_type, *args, **kwargs):
        model_class = self.models.get(property_type)
        if not model_class:
            return redirect('error_page')

        site_slug = kwargs.get('site_slug')
        initial_site = get_object_or_404(Site, slug=site_slug)
        # latest_record = model_class.objects.filter(site=initial_site).order_by('-created').first()
        period = YearMonth.objects.get(pk=request.POST.get('period'))
        latest_record = model_class.objects.filter(site=initial_site, changed_by=request.user,
                                                   period=period).order_by('-created').first()

        PropertyForm = get_universal_property_form(model_class)
        form = PropertyForm(request.POST, request.FILES, instance=latest_record)

        if form.is_valid():
            instance = form.save(commit=False)
            # Handle document retention
            if not form.cleaned_data.get('document') and latest_record and latest_record.document:
                instance.document = latest_record.document
            instance.save()
            form.save_m2m()  # Save many-to-many data

            # Mass change logic: Check if a mine or shaft is selected and apply changes accordingly
            mine = form.cleaned_data.get('mine')
            shaft = form.cleaned_data.get('shaft')
            if mine:
                sites = Site.objects.filter(shaft__mine=mine)
            elif shaft:
                sites = Site.objects.filter(shaft=shaft)
            else:
                sites = [initial_site]

            for site in sites:
                if site != initial_site:  # Avoid duplicating for the initial site
                    # Prepare data for model creation, excluding non-model fields
                    model_data = {key: value for key, value in form.cleaned_data.items() if
                                  key in [field.name for field in model_class._meta.fields]}
                    model_data['site'] = site
                    if not form.cleaned_data.get('document'):
                        model_data['document'] = instance.document  # Retain the document from the instance
                    # Create a new property instance for each site with the adjusted data
                    property_instance = model_class(**model_data)
                    property_instance.save()
                # if site != initial_site:  # Avoid duplicating for the initial site
                #     # Create a copy of form.cleaned_data and update the 'site' key
                #     property_data = form.cleaned_data.copy()
                #     property_data['site'] = site
                #
                #     if not property_data.get('document'):
                #         # If 'document' key is not in property_data or the value is None,
                #         # retain the document from the latest_record if it exists
                #         property_data['document'] = latest_record.document if latest_record and latest_record.document\
                #                                                             else property_data.get('document')
                #
                #     # Create a new property instance with the updated data
                #     property_instance = model_class(**property_data)
                #     property_instance.save()

            # for site in sites:
            #     if site != initial_site:  # Avoid duplicating for the initial site
            #         property_instance = model_class(**form.cleaned_data, site=site)
            #         if not form.cleaned_data.get('document'):
            #             property_instance.document = instance.document  # Retain the document from the instance
            #         property_instance.save()

            # Redirect to the site detail page, or wherever is appropriate.
            return HttpResponseRedirect(reverse('site_detail', kwargs={'site_slug': kwargs.get('site_slug')}))
        else:
            # If the form is not valid, re-render the page with the form errors.
            return render(request, 'universal_property_form.html', {'form': form, 'site_slug': site_slug})


def edit_property_view(request, site_slug, model_name, property_id):
    site = get_object_or_404(Site, slug=site_slug)
    ModelClass = apps.get_model('cars', model_name)  # Replace 'app_name' with your actual app name
    instance = get_object_or_404(ModelClass, id=property_id)

    if request.method == 'POST':
        # form = PropertyEditForm(request.POST, instance=instance, model_class=ModelClass)
        form = PropertyEditForm(request.POST or None, instance=instance, model_class=ModelClass)

        if form.is_valid():
            form.save()
            return redirect('site_detail', site_slug=site_slug)  # Redirect back to the site detail page
    else:
        form = PropertyEditForm(instance=instance, model_class=ModelClass)

    return render(request, 'edit_property.html', {'form': form, 'site': site})

# def edit_property(request, site_id, model_name, property_id):
#     # Map model names to model classes
#     model_mapping = {
#         'plan_zadanie': Plan_zadanie,
#         'plotnost_gruza': Plotnost_gruza,
#         # Add the rest of the mappings
#     }
#     model_class = model_mapping.get(model_name)
#     if not model_class:
#         return HttpResponseNotFound('Model not found')
#
#     instance = get_object_or_404(model_class, id=property_id)
#
#     if request.method == 'POST':
#         form = PropertyEditForm(request.POST, instance=instance, model_class=model_class)
#         if form.is_valid():
#             form.save()
#             return redirect('site_detail', site_id=site_id)  # Adjust as needed to redirect back to the detail view
#     else:
#         form = PropertyEditForm(instance=instance, model_class=model_class)
#
#     return render(request, 'edit_property.html', {'form': form})

def mines_list(request):
    mines = Mine.objects.all()
    return render(request, 'mines_list.html', {'mines': mines,'menu':menu})


def shafts_list(request, mine_slug):
    mine = get_object_or_404(Mine, slug=mine_slug)
    shafts = Shaft.objects.filter(mine=mine)
    return render(request, 'shafts_list.html', {'mine': mine, 'shafts': shafts,'menu':menu})


def sites_list(request, shaft_slug):
    shaft = get_object_or_404(Shaft, slug=shaft_slug)
    sites = Site.objects.filter(shaft=shaft)
    return render(request, 'sites_list.html', {'shaft': shaft, 'sites': sites,'menu':menu})


def site_detail(request, site_slug):
    site = get_object_or_404(Site, slug=site_slug)

    absolute_shaft_url = f"{reverse('sites_list', kwargs={'shaft_slug': site.shaft.slug})}"
    shaft_link = f'<a href="{absolute_shaft_url}">{site.shaft.title}</a>'

    absolute_mine_url = f"{reverse('shafts_list', kwargs={'mine_slug': site.shaft.mine.slug})}"
    mine_link = f'<a href="{absolute_mine_url}">{site.shaft.mine.title}</a>'

    context = {
        'title': f"{site_slug}",
        'menu': menu,
        'site': site,
        'shaft_link': shaft_link,
        'mine_link': mine_link,
    }
    return render(request,'site_detail.html',context=context)

def get_hierarchical_data():
    return Mine.objects.prefetch_related('shaft_set__site_set').all()

class HierarchicalListView(ListView):
    model = Mine
    template_name = 'hierachy.html'
    context_object_name = 'mines'

    def get_queryset(self):
        return get_hierarchical_data()

# menu = ['О сайте',"Добавить машину", "Обратная связь", "Войти"]
menu = [
    {'title': 'О сайте', 'url_name': 'about'},
    {'title': "Добавить машину", 'url_name': 'add_page'},
    # {'title': "Обратная связь", 'url_name': 'contact'},
    # {'title': "Войти", 'url_name': 'login'},
]
class MyClass:
    def __init__(self,a,b):
        self.a = a
        self.b = b


data_db = [
{'id': 1, 'title':'Sandvik', 'content': '''
Грузовик Toro™ TH545i представляет собой высокопроизводительный подземный самосвал грузоподъемностью 45 тонн и предназначен для работы в выработках сечением 4,5 x 4,5 метра. Его превосходная производительность основана на проверенной конструкции, мощном двигателе и высоком отношении полезной нагрузки к весу.
''', 'is_published':True},
{'id': 2, 'title':'Maggot', 'content': 'Жыл был маленький уродский червячок', 'is_published':False},
{'id': 3, 'title':'Cat', 'content':'''
A Reliable Truck with Emission Control Options
The Cat® AD45 Underground Truck delivers all the power, performance and reliability you expect from the AD45 — but the latest model also offers an an advanced EU Stage V compliant engine and aftertreatment solution that meets the strictest emissions standards, lowers your carbon footprint and improves air quality in your mine. In addition, a retrofit solution is available that allows you to retrofit the previous model, the AD45B, to meet the same strict standards. This ultra-clean diesel machine delivers superior productivity thanks to its ideal match with the next generation Cat R1700 underground loader and is technology-enhanced with features that improve productivity, boost uptime and keep operators and personnel safer on the job.
''', 'is_published':True},
]


class CarsHome(ListView):
    model = Car
    template_name = 'cars/index.html'
    context_object_name = 'post'
    extra_context = {
        'title':'Полный список машин',
        'menu':menu,
        'posts': Car.published.all().select_related('cat'),
        'cat_selected': 0,
    }


class SiteDetail(DetailView):

    model = Site  # This tells Django which model this view is about
    template_name = 'site_detail.html'
    slug_url_kwarg = 'site_slug'  # Assumes you are using slugs to identify sites

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        site = self.object
        service = SiteDataService(site=site)

        all_data = service.get_all_data()

        related_data_tables = {}
        for key, data in all_data.items():
            # Convert the lists of dictionaries ('full' and 'filtered') into HTML tables
            related_data_tables[f"{key}_all"] = self.convert_to_html(data['full'])#,classes='content-table', index=False, border=0, escape=False)
            related_data_tables[f"{key}_filtered"] = self.convert_to_html(data['filtered'])#,classes='content-table', index=False, border=0, escape=False)

        context['related_data_tables'] = related_data_tables
        return context


    def convert_to_html(self, records):
        # Assuming each record is a dictionary that you want to convert into an HTML table row
        # This is a simplistic conversion for demonstration; adjust as needed
        if not records:
            return mark_safe("<p>No records found.</p>")

        headers = records[0].keys()
        header_html = "<tr>" + "".join(f"<th>{header}</th>" for header in headers) + "</tr>"
        rows_html = format_html_join('', "<tr>" + "".join("<td>{}</td>" for _ in headers) + "</tr>",
                                     (tuple(record.values()) for record in records))

        table_html = f"<table>{header_html}{rows_html}</table>"
        return mark_safe(table_html)


class SiteUpdate(LoginRequiredMixin, UpdateView):
    model = Site
    form_class = SiteEditForm
    template_name = 'site_edit.html'
    slug_url_kwarg = 'site_slug'

    def get_context_data(self, **kwargs):
        context = super(SiteUpdate, self).get_context_data(**kwargs)
        if self.request.POST:
            formsets = [
                PlanZadanieFormset(self.request.POST, instance=self.object, prefix='planzadanie'),
                Plotnost_gruzaFormset(self.request.POST, instance=self.object, prefix='plotnostgruza'),
                Schema_otkatkiFormset(self.request.POST, instance=self.object, prefix='schemaotkatki'),
                T_smenyFormset(self.request.POST, instance=self.object, prefix='tsmeny'),
                T_regl_pereryvFormset(self.request.POST, instance=self.object, prefix='treglpereryv'),
                T_pereezdFormset(self.request.POST, instance=self.object, prefix='tpereezd'),
                T_vspomFormset(self.request.POST, instance=self.object, prefix='tvspom'),
                NsmenFormset(self.request.POST, instance=self.object, prefix='nsmen'),
            ]
        else:
            formsets = [
                PlanZadanieFormset(instance=self.object, prefix='planzadanie'),
                Plotnost_gruzaFormset(instance=self.object, prefix='plotnostgruza'),
                Schema_otkatkiFormset(instance=self.object, prefix='schemaotkatki'),
                T_smenyFormset(instance=self.object, prefix='tsmeny'),
                T_regl_pereryvFormset(instance=self.object, prefix='treglpereryv'),
                T_pereezdFormset(instance=self.object, prefix='tpereezd'),
                T_vspomFormset(instance=self.object, prefix='tvspom'),
                NsmenFormset(instance=self.object, prefix='nsmen'),
            ]
        context = dict(formsets)
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        formsets = [
            PlanZadanieFormset(self.request.POST, instance=self.object),
            Plotnost_gruzaFormset(self.request.POST, instance=self.object),
            Schema_otkatkiFormset(self.request.POST, instance=self.object),
            T_smenyFormset(self.request.POST, instance=self.object),
            T_regl_pereryvFormset(self.request.POST, instance=self.object),
            T_pereezdFormset(self.request.POST, instance=self.object),
            T_vspomFormset(self.request.POST, instance=self.object),
            NsmenFormset(self.request.POST, instance=self.object),
        ]

        if form.is_valid() and all(formset.is_valid() for formset in formsets):
            return self.form_valid(form, formsets)
        else:
            return self.form_invalid(form, formsets)

    def form_valid(self, form, formsets):
        response = super().form_valid(form)
        for formset in formsets:
            formset.instance = self.object
            formset.save()
        return response

    def form_invalid(self, form, formsets):
        return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        return reverse_lazy('site_detail', kwargs={'site_slug': self.object.slug})



class AddPage(FormView):
    form_class = AddPostForm
    template_name = 'cars/addpage.html'
    success_url = reverse_lazy('home')


def add_page(request):
    # return HttpResponse("Добавление статьи")
    if request.method == 'POST':
        form = AddPostForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = AddPostForm()

    data ={
        'menu': menu,
        'title': 'Добавить машину',
        'form': form
    }
    return render(request,'cars/addpage.html', data)

def contact(request):
    return HttpResponse("Обратная связь")

def login(request):
    return HttpResponse("Авторизация")

def show_post(request, post_slug):
    post = get_object_or_404(Car, slug=post_slug)
    data = {
        'title': post.title,
        'menu': menu,
        'post': post,
        'cat_selected':1,
    }
    return render(request, 'cars/post.html', data)




@login_required
def about(request):
    if request.method == 'POST':
        form = UploadFilesForm(request.POST, request.FILES)
        if form.is_valid():
            # handle_uploaded_file(form.cleaned_data['file'])
            fp = UploadFiles(file=form.cleaned_data['file'])
            fp.save()
    else:
        form = UploadFilesForm()
    return render(request,'cars/about.html', {'title': 'О сайте', 'menu:': menu, 'form': form})


def cars(request, car_id):
    return HttpResponse(f'<h1>Страница справочников машин</h1><p>id: {car_id}</p>')

def cars_by_producer(request, car_slug):
    print(request.GET)
    return HttpResponse(f'<h1>Страница справочников машин</h1><p>slug: {car_slug}</p>')

def archive(request, year):
    if year > 2023:
        uri = reverse('cars_by_producer', args=('sandvik',))
        return HttpResponseRedirect(uri)
    return HttpResponse(f"<h1>Архив по годам</h1><p>{year}</p>")

def page_not_found(request, exception):
    return HttpResponseNotFound('<H1>Эээ, брат, ты не в ту дверь зашёл да ?</H1>')


def show_category(request, cat_slug):
    category = get_object_or_404(Category, slug=cat_slug)
    posts = Car.published.filter(cat_id=category.pk)
    # cat_selected = cat_id if cat_id is not None else 0

    data = {
        'title': f'Рубрика:{category.name}',
        'menu': menu,
        'posts': posts,
        'cat_selected': category.pk,
    }
    return render(request, 'cars/index.html', context=data)

def show_tag_postlist(request, tag_slug):
    tag = get_object_or_404(TagPost, slug=tag_slug)
    posts = tag.tags.filter(is_published=Car.Status.PUBLISHED)

    data = {
        'title':f"Тег: {tag.tag}",
        'menu': menu,
        'posts': posts,
        'cat_selected': None,
    }

    return render(request, 'car/index.html', context=data)


def places(request):
    queryset = Site.objects.select_related('shaft__mine')
    data = []

    for site in queryset:

        absolute_site_url = f"{reverse('site_detail', kwargs={'site_slug': site.slug})}"
        site_link = f'<a href="{absolute_site_url}">{site.title}</a>'

        absolute_shaft_url = f"{reverse('sites_list', kwargs={'shaft_slug': site.shaft.slug})}"
        shaft_link = f'<a href="{absolute_shaft_url}">{site.shaft.title}</a>'

        absolute_mine_url = f"{reverse('shafts_list', kwargs={'mine_slug': site.shaft.mine.slug})}"
        mine_link = f'<a href="{absolute_mine_url}">{site.shaft.mine.title}</a>'

        data.append({
            'Рудник': mine_link,#site.shaft.mine.title,
            'Шахта': shaft_link,#site.shaft.title,
            'Участок': site_link,
        })
    df = pd.DataFrame(data)

    html_table = df.to_html(index=False,
                            border=0,
                            justify='center',
                            classes='content-table',
                            render_links=True,
                            escape=False,
                            )
    data = {'title': "Места расстановки:",
        'menu': menu,
        'mines' : Mine.objects.all(),
        'shafts' : Shaft.objects.all(),
        'sites' : Site.objects.all(),
        'df': html_table,
    }
    return render(request, 'places.html', context=data)


def mine_detail():
    return None


def shaft_detail():
    return None


