from django.contrib import admin
from .models import Car, Category, Mine, Shaft, Site, YearMonth, Plan_zadanie, Placement, PlacementCar, Plotnost_gruza, \
    Schema_otkatki, T_smeny, T_regl_pereryv, T_pereezd, T_vspom, Nsmen, Kuzov_Coeff_Zapl, V_Skorost_dvizh, T_pogruzki, \
    T_razgruzki
from simple_history.admin import SimpleHistoryAdmin


@admin.register(Car)
class CarAdmin (SimpleHistoryAdmin):
    list_display =('artikul','title', 'time_create', 'time_update', 'is_published','cat','breaf_info')
    list_display_links = ('artikul','title')
    ordering = ['time_create','title']
    list_editable = ['is_published','cat']
    list_per_page = 50
    search_fields = ['title', 'cat__name']
    list_filter = ['cat__name', 'is_published']

    @admin.display(description="Описание")
    def breaf_info(self, cars: Car):
        return f"Текст {len(cars.content)} символов"

@admin.register(Category)
class CarAdmin (SimpleHistoryAdmin):
    list_display =('id','name')
    list_display_links = ('id','name')

    # ordering = ['time_create','title']


@admin.register(Plan_zadanie)
class CarAdmin(SimpleHistoryAdmin):
    list_display = ('id','value','period', 'site')
    list_display_links = ('id','value','period', 'site')
    history_list_display = ['site','value']

@admin.register(Mine)
class CarAdmin (SimpleHistoryAdmin):
    list_display =('id','title','slug')
    list_display_links = ('id','title','slug')


@admin.register(Shaft)
class CarAdmin (SimpleHistoryAdmin):
    list_display =('id','title','mine_id','slug')
    list_display_links = ('id','title','slug')
    # list_display_links = ('mine_id', 'title')

@admin.register(Site)
class CarAdmin (SimpleHistoryAdmin):
    list_display =('id','title','shaft_id','slug')#,'get_latest_value')
    list_display_links = ('id','title','shaft_id','slug')#,'get_latest_value')
    # history_list_display = ['get_latest_qpl_history']

    # def get_latest_value(self, obj):
    #     return obj.plan_zadanie.Qpl if obj.plan_zadanie else None

    # get_latest_value.short_description = 'последнее занчение'

    # def get_latest_value_history(self, history):
    #     return history.instance.plan_zadanie.Qpl if history.instance.plan_zadanie else None
    #
    # get_latest_qpl_history.short_description = 'Qpl at Revision'


@admin.register(YearMonth)
class CarAdmin (SimpleHistoryAdmin):
    list_display =('id','title','year','month')
    # list_display_links = ('id','title','year','month')
    list_editable = ['year','month']

@admin.register(Placement)
class CarAdmin (SimpleHistoryAdmin):
    list_display =('id','created','changed_by','site','period')
    list_display_links = ('id','created',)
    list_editable = ['changed_by','site','period']

@admin.register(PlacementCar)
class CarAdmin (SimpleHistoryAdmin):
    list_display =('id','car','placement')
    list_display_links = ('id',)
    list_editable = ['car','placement']


@admin.register(Plotnost_gruza)
class CarAdmin(SimpleHistoryAdmin):
    list_display = ('id','value','period', 'site')
    list_display_links = ('id','value','period', 'site')
    history_list_display = ['site','value']

@admin.register(Schema_otkatki)
class CarAdmin(SimpleHistoryAdmin):
    list_display = ('id','value','period', 'site')
    list_display_links = ('id','value','period', 'site')
    history_list_display = ['site','value']

@admin.register(T_smeny)
class CarAdmin(SimpleHistoryAdmin):
    list_display = ('id','value','period', 'site')
    list_display_links = ('id','value','period', 'site')
    history_list_display = ['site','value']

@admin.register(T_regl_pereryv)
class CarAdmin(SimpleHistoryAdmin):
    list_display = ('id','value','period', 'site')
    list_display_links = ('id','value','period', 'site')
    history_list_display = ['site','value']


@admin.register(T_pereezd)
class CarAdmin(SimpleHistoryAdmin):
    list_display = ('id','value','period', 'site')
    list_display_links = ('id','value','period', 'site')
    history_list_display = ['site','value']


@admin.register(T_vspom)
class CarAdmin(SimpleHistoryAdmin):
    list_display = ('id','value','period', 'site')
    list_display_links = ('id','value','period', 'site')
    history_list_display = ['site','value']


@admin.register(Nsmen)
class CarAdmin(SimpleHistoryAdmin):
    list_display = ('id','value','period', 'site')
    list_display_links = ('id','value','period', 'site')
    history_list_display = ['site','value']


@admin.register(Kuzov_Coeff_Zapl)
class CarAdmin(SimpleHistoryAdmin):
    list_display = ('id','value','period', 'site')
    list_display_links = ('id','value','period', 'site')
    history_list_display = ['site','value']


@admin.register(V_Skorost_dvizh)
class CarAdmin(SimpleHistoryAdmin):
    list_display = ('id','value','period', 'site')
    list_display_links = ('id','value','period', 'site')
    history_list_display = ['site','value']


@admin.register(T_pogruzki)
class CarAdmin(SimpleHistoryAdmin):
    list_display = ('id','value','period', 'site')
    list_display_links = ('id','value','period', 'site')
    history_list_display = ['site','value']


@admin.register(T_razgruzki)
class CarAdmin(SimpleHistoryAdmin):
    list_display = ('id','value','period', 'site')
    list_display_links = ('id','value','period', 'site')
    history_list_display = ['site','value']