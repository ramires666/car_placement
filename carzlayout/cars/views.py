from collections import defaultdict
from django.db.models.functions import Concat


from django import forms
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.db.models import F, OuterRef, Subquery, Prefetch, Value, CharField
from django.forms import model_to_dict,ModelForm
from django.http import HttpResponse, HttpResponseNotFound, Http404, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy, resolve
from django.template.loader import render_to_string
# from django.template.defaultfilters import slugify
from pytils.translit import slugify

from django.utils.timezone import now
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView, DetailView, FormView, UpdateView, CreateView
from cars.models import Mine, Shaft, Site, Plan_zadanie, Plotnost_gruza, Schema_otkatki, T_smeny, T_regl_pereryv, \
    T_pereezd, T_vspom, Nsmen, YearMonth, V_objem_kuzova, Kuzov_Coeff_Zapl, V_Skorost_dvizh, T_pogruzki, T_razgruzki, \
    Ktg, Placement, PlacementCar
from .forms import SiteEditForm, PlanZadanieFormset, Plotnost_gruzaFormset, Schema_otkatkiFormset, T_smenyFormset, \
    T_regl_pereryvFormset, T_pereezdFormset, T_vspomFormset, NsmenFormset, PropertyEditForm, UniversalPropertyForm, \
    KtgForm, PlacementForm, PlacementCarForm
from itertools import chain
from django.apps import apps


from cars.forms import AddPostForm, UploadFilesForm, SiteEditForm, get_universal_property_form
from cars.models import Car, Category, TagPost, UploadFiles

import pandas as pd
from django.conf import settings
from .site_data_service import SiteDataService
from django.utils.html import format_html_join, mark_safe

from django.utils import timezone
from django.db import transaction


class CarListView(ListView):
    model = Car
    template_name = 'car_list.html'
    context_object_name = 'cars'
    queryset = Car.objects.filter(is_published=Car.Status.PUBLISHED)  # Show only published cars


def list_cars(request):
    # Subquery to get the most recent KTG value for each car
    latest_ktg_subquery = Ktg.objects.filter(
        car=OuterRef('pk')
    # ).order_by('-period__date', '-created').values('KTG')[:1]
    ).order_by('-period__year', '-period__month', '-created').values('KTG')[:1]


    # Fetch all cars from the database, annotating each with its category name and the most recent KTG value
    cars = Car.objects.annotate(
        category_title=F('cat__name'),
        latest_ktg=Subquery(latest_ktg_subquery)
    ).values(
        'title', 'V_objem_kuzova', 'category_title', 'latest_ktg'
    )

    # Convert the cars queryset into a DataFrame
    cars_df = pd.DataFrame(list(cars))

    # Convert the DataFrame to an HTML table
    cars_html_table = cars_df.to_html(classes=["table", "table-striped"], index=False)

    # Pass the HTML table to the template
    context = {'cars_html_table': cars_html_table}
    return render(request, 'cars/cars_list.html', context)


class CarDetailView(DetailView):
    model = Car
    template_name = 'car_detail.html'
    context_object_name = 'car'
    # Assuming your Car model has a 'slug' field for URL routing
    slug_url_kwarg = 'car_slug'


@csrf_exempt
def update_ktg(request, car_slug):
    if request.method == 'POST':
        car = get_object_or_404(Car, slug=car_slug)
        # Assume you're receiving a year, month, and KTG value from the form
        # year = request.POST.get('year')

        period = request.POST.get('period')

        ktg_value = request.POST.get('ktg_value').replace(',', '.')
        document = request.FILES.get('document')
        # Fetch the YearMonth instance using period_id
        period_instance = get_object_or_404(YearMonth, pk=period)

        ktg_record = Ktg.objects.create(
            car=car,
            KTG=ktg_value,  # Ensure this field name matches your model's field name
            period=period_instance,  # Assign the fetched YearMonth instance here
            document=document,
            changed_by = request.user,  # Set the current user

        )

        if ktg_record:
            response_message = "KTG record created successfully."
            # Convert ktg_record to a dict excluding non-serializable fields
            ktg_data = model_to_dict(ktg_record, exclude=["document"])
            # If you need to include the document URL, do it separately
            ktg_data["document_url"] = ktg_record.document.url if ktg_record.document else None
        else:
            response_message = "KTG record update failed."  # Adjust according to your logic

    return JsonResponse({"success": response_message, "ktg_data": ktg_data})


def get_ktg_data_for_car(car_id):
    # Prefetch YearMonth objects to reduce database hits
    year_months = YearMonth.objects.all().prefetch_related(
        Prefetch('ktg_set', queryset=Ktg.objects.filter(car_id=car_id), to_attr='ktgs')
    )

    ktg_data = defaultdict(lambda: {str(month): None for month in range(1, 13)})  # Defaultdict with months

    for ym in year_months:
        for ktg in getattr(ym, 'ktgs', []):
            ktg_data[ym.year][str(ym.month)] = ktg.KTG

    return ktg_data


def car_detail(request, car_slug):
    car = get_object_or_404(Car, slug=car_slug)
    V_objem_kuzova = car.V_objem_kuzova
    ktg_records = Ktg.objects.filter(car=car).order_by('-period__year', '-period__month','-created')
    year_months = YearMonth.objects.all().order_by('-year', 'month')
    current_year = now().year


    # Initially set ktg_html_table and most_recent_ktg to default values
    ktg_html_table = "<p>No KTG records found for this car.</p>"
    most_recent_ktg = {'KTG': 0, 'document': None}  # Default values for the form
    month_names = dict(YearMonth.Month.choices)

    if ktg_records.exists():  # Check if there are any KTG records
        # ktg_df = pd.DataFrame(list(ktg_records.values('period__year', 'period__month', 'KTG', 'document')))
        ktg_df = pd.DataFrame(list(ktg_records.values('period__year', 'period__month', 'KTG')))

        # ktg_df = ktg_df.pivot(index='period__year', columns='period__month', values='KTG').fillna('')
        ktg_df = ktg_df.pivot_table(index='period__year', columns='period__month', values='KTG',aggfunc='first').fillna('')

        if not ktg_df.empty:
            full_table = ktg_df.copy()

            # Latest records for each month of the current year
            latest_records_df = ktg_df.loc[current_year:current_year] if current_year in ktg_df.index else pd.DataFrame()

            full_table.rename(columns=month_names,inplace=True)
            latest_records_df.rename(columns=month_names,inplace=True)

            latest_records_df.columns.name=current_year

            # Convert DataFrames to HTML tables
            full_html_table = full_table.to_html(
                                                header=True,
                                                index_names=False, #ugly two layer index names
                                                index=True,
                                                border=0,
                                                justify='center',
                                                classes='content-table',
                                                render_links=True,
                                                escape=False)


            latest_html_table = latest_records_df.to_html(
                                                header=True,
                                                index_names=True,
                                                index=False,
                                                border=0,
                                                justify='center',
                                                classes='content-table',
                                                render_links=True,
                                                escape=False)


        else:
            ktg_df.rename(columns=month_names,inplace=True)

            ktg_html_table = ktg_df.to_html(index=True,
                                            border=0,
                                            justify='center',
                                            classes='content-table',
                                            render_links=True,
                                            escape=False)
            full_html_table = ktg_html_table
            latest_html_table = ktg_html_table

    context = {
        'car': car,
        'V_objem_kuzova': V_objem_kuzova,
        'full_ktg_table': full_html_table,
        'latest_ktg_table': latest_html_table,
        'current_year': current_year,
        # 'ktg_html_table': ktg_html_table,
        # 'most_recent_ktg': most_recent_ktg,  # Pass the most recent KTG or default values to the template
        'year_months': year_months,
    }
    return render(request, 'car_detail.html', context)


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

PROPERTY_SLUYGIFYED_MODEL_MAP = {
    'plan-zadanie': Plan_zadanie,
    'plotnost-gruza': Plotnost_gruza,
    'plecho-otkatki': Schema_otkatki,
    'dlitelnost-smenyi': T_smeny,
    'reglamentpereryivyi': T_regl_pereryv,
    'vremya-pereezda': T_pereezd,
    'vremya-vspomogat': T_vspom,
    'kol-vo-smnen': Nsmen,
    'obem-kuzova': V_objem_kuzova,
    'koeff-zapoln-kuzova': Kuzov_Coeff_Zapl,
    'skorost-dvizheniya': V_Skorost_dvizh,
    'vremya-pogruzki': T_pogruzki,
    'vremya-razgr': T_razgruzki,
}

def render_df2html(last_10_records):
    columns = {
        'value': pd.Series(dtype='float'),
        'period_id': pd.Series(dtype='object'),  # Use 'object' for strings and mixed types
        'changed_by_id': pd.Series(dtype='object'),
        'created': pd.Series(dtype='datetime64[ns]'),  # Use 'datetime64[ns]' for datetime columns
        'document': pd.Series(dtype='object'),
    }
    df10 = pd.DataFrame(columns)

    if last_10_records.exists():
        df10 = pd.DataFrame(list(last_10_records.values()))


    period_titles = YearMonth.objects.in_bulk(list(df10['period_id']))
    # Assuming User model for changed_by

    # Adjusted to exclude None values
    changed_by_ids = [id for id in df10['changed_by_id'] if pd.notnull(id) and not pd.isna(id)]

    user_names = User.objects.in_bulk(changed_by_ids)

    # Map period_id to period title
    df10['period_id'] = df10['period_id'].map(lambda x: period_titles[x].title if x in period_titles else None)

    # Map changed_by_id to user name (you can adjust this to use first_name, last_name, etc.)
    df10['changed_by_id'] = df10['changed_by_id'].map(
        lambda x: user_names[x].get_full_name() if x in user_names else None)
    df10['created'] = df10['created'].dt.strftime('%Y-%m-%d %H:%M')
    df10 = df10[['value','period_id','created','changed_by_id','document']]
    df10['document'] = df10['document'].apply(lambda x: f"<a href=/media/{x} class=open-modal>{x.split('/')[-1]}</a>" if pd.notnull(x) else '')
    df10.columns = ['Значение','Период','Внесено','Автор','Обоснование']


    df10html_table = df10.to_html(
        header=True,
        index_names=True,  # ugly two layer index names
        index=True,
        border=0,
        justify='center',
        classes='content-table',
        render_links=True,
        escape=False)
        # classes=["table", "table-bordered", "table-striped"], index=False)

    return df10html_table


@login_required
def edit_property(request, mine_slug, shaft_slug, site_slug, property_slug, period_id=None):
    user = request.user
    site = get_object_or_404(Site, slug=f"{mine_slug}-{shaft_slug}-{site_slug}")#, shaft=shaft)

    if period_id:
        current_period = YearMonth.objects.get(id=period_id)
    else:
        current_year = timezone.now().year
        current_month = timezone.now().month
        current_period = YearMonth.objects.get(year=current_year, month=current_month)

    # Fetch the correct model based on the property name
    PropertyModel = PROPERTY_SLUYGIFYED_MODEL_MAP.get(property_slug)
    if not PropertyModel:
        raise Http404("Property model not found")

    # Fetch the latest property instance for the given site and period
    property_instance = PropertyModel.objects.filter(site=site, period=current_period).order_by('created').last()
    # Get the appropriate form class
    PropertyForm = get_universal_property_form(PropertyModel)

    if request.method == 'POST':
        form = PropertyForm(request.POST, request.FILES, user=request.user)
        form.instance.changed_by = request.user
        if form.is_valid():

            # The period should be fetched from the form
            selected_period = form.cleaned_data['period']
            overwrite = form.cleaned_data.get('overwrite_existing', False)
            # overwrite = form.cleaned_data.get('overwrite_existing', False)

            with transaction.atomic():
                if form.cleaned_data['mine']:
                    mine_ = form.cleaned_data['mine'].slug
                    target_sites = Site.objects.filter(shaft__mine__slug=mine_)
                elif form.cleaned_data['shaft']:
                    shaft_ = form.cleaned_data['shaft'].slug
                    target_sites = Site.objects.filter(shaft__slug=shaft_)
                else:
                    target_sites = [site]

                if selected_period.month == 0:
                    # Handle whole year: iterate through all months
                    save_property_for_whole_year(form, target_sites, selected_period, overwrite, PropertyModel)
                else:
                    # Handle specific month
                    save_property_value(form, target_sites, selected_period, overwrite, PropertyModel)

            return redirect('places')

    else:
        if not property_instance:
            initial_data = {
                'site': site,
                'period': current_period,
                'changed_by': request.user,
            }
            form = PropertyForm(initial=initial_data)
        else:
            form = PropertyForm(instance=property_instance, user=request.user)

    form.fields['changed_by'].disabled = True  # Disable for non-admin user


    last_10_records = PropertyModel.objects.filter(site=site).order_by('-created')[:10]
    df10html_table = render_df2html(last_10_records)

    context = {
        'form': form,
        'property_name_verbose': PropertyModel._meta.verbose_name,
        'last_10_records': df10html_table,
        'tab': '\t',
    }
    return render(request, 'edit_property.html', context)


def save_property_for_whole_year(form, target_sites, year_period, overwrite, PropertyModel):
    """
    Saves a property value for the whole year with month=0.
    """
    # Ensure we get or create a period for the whole year with month=0.
    period, created = YearMonth.objects.get_or_create(year=year_period.year, month=0)

    # Call the function to save the property value for the whole year period.
    save_property_value(form, target_sites, period, overwrite, PropertyModel)

    # """
    # Distributes a property value across all months of the selected year.
    # """
    # for month in range(1, 13):
    #     # Ensure we get or create a period for each month within the given year.
    #     period, created = YearMonth.objects.get_or_create(year=year_period.year, month=month)
    #
    #     # Call the function to save the property value for the current period.
    #     save_property_value(form, target_sites, period, overwrite, PropertyModel)


def save_property_value(form, target_sites, period, overwrite, PropertyModel):
    """
    Save or update property values for given sites and period.
    """
    # Ensure PropertyModel is actually a model class and not mistakenly a boolean or other type.
    if not callable(PropertyModel):
        raise ValueError(f"PropertyModel is not callable. Received: {PropertyModel}")

    for target_site in target_sites:
        if not overwrite:
            # Check if a property record for the given period already exists.
            exists = PropertyModel.objects.filter(site=target_site, period=period).exists()
            if exists:
                # Skip creating a new record if one already exists and we're not overwriting.
                continue

        # Prepare model data excluding specific form fields and csrfmiddlewaretoken.
        model_data = {k: v for k, v in form.cleaned_data.items() if
                      k not in ['shaft', 'mine', 'site', 'period', 'overwrite_existing', 'csrfmiddlewaretoken']}

        # Create and save a new record for the property model.
        model_data['changed_by'] = form.instance.changed_by

        # Create and save the new record
        new_record = PropertyModel(site=target_site, period=period, **model_data)
        new_record.save()

# def save_property_for_whole_year(form, site, year_period, overwrite, PropertyModel):
#     # Implement the logic to distribute a property value across all months of the selected year
#     for month in range(1, 13):
#         period, _ = YearMonth.objects.get_or_create(year=year_period.year, month=month)
#         save_property_value(form, site, period, PropertyModel, overwrite)
#
# def save_property_value(form, target_sites, period, overwrite, PropertyModel):
#     """
#     Save or update property values for given sites and period.
#     """
#     for target_site in target_sites:
#         if not overwrite:
#             exists = PropertyModel.objects.filter(site=target_site, period=period).exists()
#             if exists:
#                 continue
#
#         model_data = {k: v for k, v in form.cleaned_data.items() if k not in ['shaft', 'mine', 'site', 'period', 'overwrite_existing', 'csrfmiddlewaretoken']}
#         new_record = PropertyModel(site=target_site, period=period, **model_data)
#         new_record.save()


class UniversalPropertyView(View):
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
            form = PropertyForm(initial=initial_data, user=request.user)  # instantiate the form class
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

        PropertyForm = get_universal_property_form(model_class, user=request.user)
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
    context_object_name = 'car'
    extra_context = {
        'title':'Полный список машин',
        'menu':menu,
        'cars': Car.published.all().select_related('cat'),
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

def show_car(request, car_slug):
    car = get_object_or_404(Car, slug=car_slug)
    data = {
        'title': car.title,
        'menu': menu,
        'car': car,
        'cat_selected':1,
    }
    return render(request, 'cars/car.html', data)




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
    cars = Car.published.filter(cat_id=category.pk)
    # cat_selected = cat_id if cat_id is not None else 0

    data = {
        'title': f'Рубрика:{category.name}',
        'menu': menu,
        'cars': cars,
        'cat_selected': category.pk,
    }
    return render(request, 'cars/index.html', context=data)

def show_tag_postlist(request, tag_slug):
    tag = get_object_or_404(TagPost, slug=tag_slug)
    cars = tag.tags.filter(is_published=Car.Status.PUBLISHED)

    data = {
        'title':f"Тег: {tag.tag}",
        'menu': menu,
        'cars': cars,
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
    return render(request, 'places1.html', context=data)



def places1(request, period_id=None):
    periods = YearMonth.objects.all().order_by('year', 'month')
    if period_id:
        current_period = YearMonth.objects.get(id=period_id)
    else:
        current_period = periods.last()
    yearly_period = YearMonth.objects.filter(year=current_period.year, month=0).first()

    current_index = list(periods).index(current_period)
    previous_period = periods[current_index - 1] if current_index > 0 else None
    next_period = periods[current_index + 1] if current_index < len(periods) - 1 else None

    # Define prefetch queries for both monthly and yearly data across multiple properties
    properties_prefetch = [
        Prefetch('plan_zadanie_set', queryset=Plan_zadanie.objects.filter(period=current_period), to_attr='plan_zadanie_monthly'),
        Prefetch('plan_zadanie_set', queryset=Plan_zadanie.objects.filter(period=yearly_period), to_attr='plan_zadanie_yearly'),
        Prefetch('plotnost_gruza_set', queryset=Plotnost_gruza.objects.filter(period=current_period), to_attr='plotnost_gruza_monthly'),
        Prefetch('plotnost_gruza_set', queryset=Plotnost_gruza.objects.filter(period=yearly_period), to_attr='plotnost_gruza_yearly'),
        Prefetch('schema_otkatki_set', queryset=Schema_otkatki.objects.filter(period=current_period), to_attr='schema_otkatki_monthly'),
        Prefetch('schema_otkatki_set', queryset=Schema_otkatki.objects.filter(period=yearly_period), to_attr='schema_otkatki_yearly'),
        Prefetch('t_smeny_set', queryset=T_smeny.objects.filter(period=current_period), to_attr='t_smeny_monthly'),
        Prefetch('t_smeny_set', queryset=T_smeny.objects.filter(period=yearly_period), to_attr='t_smeny_yearly'),
        Prefetch('t_regl_pereryv_set', queryset=T_regl_pereryv.objects.filter(period=current_period), to_attr='t_regl_pereryv_monthly'),
        Prefetch('t_regl_pereryv_set', queryset=T_regl_pereryv.objects.filter(period=current_period), to_attr='t_regl_pereryv_yearly'),
        Prefetch('t_pereezd_set', queryset=T_pereezd.objects.filter(period=current_period), to_attr='t_pereezd_monthly'),
        Prefetch('t_pereezd_set', queryset=T_pereezd.objects.filter(period=current_period), to_attr='t_pereezd_yearly'),
        Prefetch('t_vspom_set', queryset=T_vspom.objects.filter(period=current_period), to_attr='t_vspom_monthly'),
        Prefetch('t_vspom_set', queryset=T_vspom.objects.filter(period=current_period), to_attr='t_vspom_yearly'),
        Prefetch('nsmen_set', queryset=Nsmen.objects.filter(period=current_period), to_attr='nsmen_monthly'),
        Prefetch('nsmen_set', queryset=Nsmen.objects.filter(period=current_period), to_attr='nsmen_yearly'),
        Prefetch('v_objem_kuzova_set', queryset=V_objem_kuzova.objects.filter(period=current_period), to_attr='v_objem_kuzova_monthly'),
        Prefetch('v_objem_kuzova_set', queryset=V_objem_kuzova.objects.filter(period=current_period), to_attr='v_objem_kuzova_yearly'),
        Prefetch('kuzov_coeff_zapl_set', queryset=Kuzov_Coeff_Zapl.objects.filter(period=current_period), to_attr='kuzov_coeff_zapl_monthly'),
        Prefetch('kuzov_coeff_zapl_set', queryset=Kuzov_Coeff_Zapl.objects.filter(period=current_period), to_attr='kuzov_coeff_zapl_yearly'),
        Prefetch('v_skorost_dvizh_set', queryset=V_Skorost_dvizh.objects.filter(period=current_period), to_attr='v_skorost_dvizh_monthly'),
        Prefetch('v_skorost_dvizh_set', queryset=V_Skorost_dvizh.objects.filter(period=current_period), to_attr='v_skorost_dvizh_yearly'),
        Prefetch('t_pogruzki_set', queryset=T_pogruzki.objects.filter(period=current_period), to_attr='t_pogruzki_monthly'),
        Prefetch('t_pogruzki_set', queryset=T_pogruzki.objects.filter(period=current_period), to_attr='t_pogruzki_yearly'),
        Prefetch('t_razgruzki_set', queryset=T_razgruzki.objects.filter(period=current_period), to_attr='t_razgruzki_monthly'),
        Prefetch('t_razgruzki_set', queryset=T_razgruzki.objects.filter(period=current_period), to_attr='t_razgruzki_yearly'),

    ]

    # sites = Site.objects.all()
    sites = Site.objects.prefetch_related(*properties_prefetch)

    data = []
    # Constructing data list for the DataFrame, to access both monthly and yearly data:
    for site in sites:
        site_data = {
            'Рудник': site.shaft.mine.title,
            'Шахта': site.shaft.title,
            'Участок': site.title,
            'План задание': (site.plan_zadanie_monthly[0].value if site.plan_zadanie_monthly else None) or
                            (site.plan_zadanie_yearly[0].value if site.plan_zadanie_yearly else None),
            'Плотность груза': (site.plotnost_gruza_monthly[0].value if site.plotnost_gruza_monthly else None) or
                            (site.plotnost_gruza_yearly[0].value if site.plotnost_gruza_yearly else None),
            'Плечо откатки': (site.schema_otkatki_monthly[0].value if site.schema_otkatki_monthly else None) or
                            (site.schema_otkatki_yearly[0].value if site.schema_otkatki_yearly else None),
            'Длительность смены': (site.t_smeny_monthly[0].value if site.t_smeny_monthly else None) or
                            (site.t_smeny_yearly[0].value if site.t_smeny_yearly else None),
            'Регламент.перерывы': (site.t_regl_pereryv_monthly[0].value if site.t_regl_pereryv_monthly else None) or
                            (site.t_regl_pereryv_yearly[0].value if site.t_regl_pereryv_yearly else None),
            'Время переезда': (site.t_pereezd_monthly[0].value if site.t_pereezd_monthly else None) or
                            (site.t_pereezd_yearly[0].value if site.t_pereezd_yearly else None),
            'Время вспомогат.': (site.t_vspom_monthly[0].value if site.t_vspom_monthly else None) or
                            (site.t_vspom_yearly[0].value if site.t_vspom_yearly else None),
            'Кол-во смнен': (site.nsmen_monthly[0].value if site.nsmen_monthly else None) or
                            (site.nsmen_yearly[0].value if site.nsmen_yearly else None),
            'Объем кузова': (site.v_objem_kuzova_monthly[0].value if site.v_objem_kuzova_monthly else None) or
                            (site.v_objem_kuzova_yearly[0].value if site.v_objem_kuzova_yearly else None),
            'КОэфф заполн. кузова': (site.kuzov_coeff_zapl_monthly[0].value if site.kuzov_coeff_zapl_monthly else None) or
                            (site.kuzov_coeff_zapl_yearly[0].value if site.kuzov_coeff_zapl_yearly else None),
            'Скорость движения': (site.v_skorost_dvizh_monthly[0].value if site.v_skorost_dvizh_monthly else None) or
                            (site.v_skorost_dvizh_yearly[0].value if site.v_skorost_dvizh_yearly else None),
            'Время погрузки': (site.t_pogruzki_monthly[0].value if site.t_pogruzki_monthly else None) or
                            (site.t_pogruzki_yearly[0].value if site.t_pogruzki_yearly else None),
            'Время разгр.': (site.t_razgruzki_monthly[0].value if site.t_razgruzki_monthly else None) or
                            (site.t_razgruzki_yearly[0].value if site.t_razgruzki_yearly else None),
        }
        data.append(site_data)

    df = pd.DataFrame(data)
    df.set_index(['Рудник', 'Шахта', 'Участок'], inplace=True)

    # Generating links as before, adjusting for the current logic
    for index, row in df.iterrows():
        rudnik, shahta, uchastok = index
        address = f"/{slugify(rudnik)}-{slugify(shahta)}-{slugify(uchastok)}/"
        for column in row.index:
            if pd.notnull(row[column]) and column not in ['Рудник', 'Шахта', 'Участок']:
                df.at[
                    index, column] = f"<a href='{address}{slugify(column)}/{current_period.id}/'><div>{row[column]}</div></a>"
            elif column not in ['Рудник', 'Шахта', 'Участок']:
                df.at[index, column] = f"<a href='{address}{slugify(column)}/{current_period.id}/'><div>-</div></a>"

    df = df.stack().unstack(level=[0, 1, 2])


    html_df = df.to_html(
                    header=True,
                    index_names=True, #ugly two layer index names
                    index=True,
                    border=0,
                    justify='center',
                    classes='content-table',
                    render_links=True,
                    escape=False)
    context = {
        'current_period': current_period,
        'previous_period': previous_period,
        'next_period': next_period,
        'site_params': html_df
    }
    return render(request, 'places.html', context)


def fetch_site_properties(site, period):
    # Define a dictionary of property models for easier access
    property_models = {
        'plan_zadanie': Plan_zadanie,
        'plotnost_gruza': Plotnost_gruza,
        'schema_otkatki': Schema_otkatki,
        't_smeny': T_smeny,
        't_regl_pereryv': T_regl_pereryv,
        't_pereezd': T_pereezd,
        't_vspom': T_vspom,
        'nsmen': Nsmen,
        'v_objem_kuzova': V_objem_kuzova,
        'kuzov_coeff_zapl': Kuzov_Coeff_Zapl,
        'v_skorost_dvizh': V_Skorost_dvizh,
        't_pogruzki': T_pogruzki,
        't_razgruzki': T_razgruzki,
    }

    properties = {}
    for prop, model in property_models.items():
        value = model.objects.filter(site=site, period=period).first()
        if not value and period.month == 0:  # If it's a yearly request and no data found, no need to look for monthly data
            properties[prop] = None
            continue
        if not value:  # If no specific month data, try to get yearly data
            yearly_period = YearMonth.objects.filter(year=period.year, month=0).first()
            value = model.objects.filter(site=site, period=yearly_period).first()
        properties[prop] = value.value if value else None  # Assuming each property model has a 'value' attribute

    return properties


def property_editor():
    pass

def mine_detail():
    return None


def shaft_detail():
    return None


class PlacementDetailView(DetailView):
    model = Placement
    template_name = 'cars/placement_detail.html'
    context_object_name = 'placement'

class PlacementUpdateView(UpdateView):
    model = Placement
    form_class = PlacementForm
    template_name = 'cars/placement_edit.html'
    success_url = reverse_lazy('placement-list')  # Adjust the URL as needed

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['cars_form'] = PlacementCarForm(self.request.POST)
        else:
            context['cars_form'] = PlacementCarForm()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        cars_form = context['cars_form']
        placement = form.save(commit=False)
        placement.changed_by = self.request.user  # Set the current user as the author
        placement.save()  # Now save the Placement instance
        form.save_m2m()  # Save any many-to-many fields on the form

        if cars_form.is_valid():
            cars_form.instance = placement
            cars_form.save()  # Save the related cars through the intermediate model PlacementCar
            # Here you may need to handle adding/removing cars to/from PlacementCar manually
        return super().form_valid(form)


class PlacementCreateView(CreateView):
    model = Placement
    form_class = PlacementForm
    template_name = 'cars/placement_create.html'
    success_url = reverse_lazy('placement-list')  # Redirect to placement list view on success

    def form_valid(self, form):
        # Save the Placement instance first without committing to the database
        placement = form.save(commit=False)
        placement.save()  # Now the Placement instance is saved and has an ID

        # Get the selected cars from the form
        cars = form.cleaned_data['cars']

        # Create PlacementCar instances for each selected car
        for car in cars:
            PlacementCar.objects.create(placement=placement, car=car)

        return super(CreateView, self).form_valid(form)

# class PlacementCreateView(CreateView):
#     # Your view definition...
#     success_url = reverse_lazy('placements')  # Make sure this matches your URL pattern name


class PlacementListView(ListView):
    model = Placement
    template_name = 'cars/placement_list.html'
    context_object_name = 'placements'

    def get_context_data(self, **kwargs):
        context = super(PlacementListView, self).get_context_data(**kwargs)
        placements = Placement.objects.select_related('site__shaft__mine', 'changed_by').annotate(
            username=Concat(F('changed_by__first_name'), Value(' '), F('changed_by__last_name')),
            site_title=F('site__title'),
            shaft_title=F('site__shaft__title'),
            mine_title=F('site__shaft__mine__title')
        ).values('id', 'created', 'username', 'site_title', 'shaft_title', 'mine_title')

        df = pd.DataFrame(list(placements))

        # Assuming 'id' is one of the columns
        df['edit_link'] = df.apply(lambda row: f'<a href="/placement/edit/{row["id"]}">Редактировать документ</a>', axis=1)

        df = df[['edit_link', 'created', 'username', 'mine_title', 'shaft_title', 'site_title']]
        # df['created'] = df['created'].dt.floor("D")
        df['created'] = df['created'].dt.strftime('%Y-%m-%d')

        df.columns = (['Редактировать','Создано','Автор','Рудник','Шахта','Участок'])

        # Select columns to display and convert DataFrame to HTML
        df_html = df.to_html(
                    header=True,
                    index_names=True, #ugly two layer index names
                    index=True,
                    border=0,
                    justify='center',
                    classes='content-table',
                    render_links=True,
                    escape=False)

        context['placements_table'] = df_html
        return context


def get_site_properties(request, site_id, period_id):
    try:
        site = Site.objects.get(pk=site_id)
        period = YearMonth.objects.get(pk=period_id)

        # Now fetch each property closest to the given period. This is an example approach.
        plan_zadanie = Plan_zadanie.objects.filter(site=site, period__lte=period).order_by('-period').first()
        plotnost_gruza = Plotnost_gruza.objects.filter(site=site, period__lte=period).order_by('-period').first()
        schema_otkatki = Schema_otkatki.objects.filter(site=site, period__lte=period).order_by('-period').first()

        data = {
            "plan_zadanie": plan_zadanie.value if plan_zadanie else "N/A",
            "plotnost_gruza": plotnost_gruza.value if plotnost_gruza else "N/A",
            "schema_otkatki": schema_otkatki.value if schema_otkatki else "N/A",
        }

        return JsonResponse(data)

    except Site.DoesNotExist:
        return JsonResponse({'error': 'Site not found'}, status=404)