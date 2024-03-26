from django.urls import path, re_path, register_converter
from cars import views
from cars.views import CarsHome, SiteDetail, SiteUpdate, edit_property_view, UniversalPropertyView, CarDetailView, \
    CarListView, update_ktg, PlacementDetailView, PlacementUpdateView, PlacementCreateView, PlacementListView, \
    get_site_properties, ajax_get_site_properties, get_latest_ktg_for_car, ajax_get_latest_ktg_for_car,\
    calc_placement

from cars import converter
# from models import Car

register_converter(converter.FourDigitYearConverter,'year4')


urlpatterns = [
    # path('',views.index, name='home'),
    path('', CarsHome.as_view(), name='home'),
    path('about/',views.about, name='about'),
    # path('cars/',views.cars,name='cars'),
    # path('cars/<int:car_id>/', views.cars,name='car_id'),
    path('cars/<int:id>/', views.cars,name='car_id'),

    # path('cars/<slug:car_slug>/', views.cars_by_producer,name='cars_by_producer'),
    # re_path(r"^archive/(?P<year>[0-9]{4})/", views.archive)
    path('archive/<year4:year>/', views.archive,name='archive'),

    path('add_page/', views.add_page, name='add_page'),
    path('contact/', views.contact, name='contact'),
    path('login/', views.login, name='login'),

    # path('cars/<slug:car_slug>/', views.show_car, name='car'),
    # path('cars/<slug:car_slug>/', CarDetailView.as_view() , name='car'),
    path('cars/<slug:car_slug>/', views.car_detail , name='car'),

    # path('update_ktg/', update_ktg, name='update_ktg'),
    path('update_ktg/<slug:car_slug>/', views.update_ktg, name='update_ktg'),


    # path('cars/', CarListView.as_view(), name='car_list'),
    path('cars/', views.list_cars, name='list_cars'),

    path('category/<slug:cat_slug>/', views.show_category, name='category'),
    path('tag/<slug:tag_slug>/', views.show_tag_postlist, name='tag'),

    path('mines/', views.mines_list, name='mines_list'),
    path('mines/<slug:mine_slug>/', views.shafts_list, name='shafts_list'),
    path('shafts/<slug:shaft_slug>/', views.sites_list, name='sites_list'),

    # path('places/',views.places1, name='places'),
    path('places/', views.places1, name='places'),
    path('places/<int:period_id>/', views.places1, name='places_with_period'),
    # path('places/',views.places, name='places'),

    # path('<str:mine>/<str:shaft>/<str:site>/', views.property_editor, name='property_editor'),
    # path('<slug:mine_slug>-<slug:shaft_slug>-<slug:site_slug>/<slug:property_slug>/', views.edit_property, name='edit_property'),
    path('<slug:mine_slug>-<slug:shaft_slug>-<slug:site_slug>/<slug:property_slug>/<int:period_id>/', views.edit_property, name='edit_property_with_period'),


    path('mine/<slug:mine_slug>/', views.mine_detail, name='mine_detail'),
    path('shaft/<slug:shaft_slug>/', views.shaft_detail, name='shaft_detail'),
    path('site/<slug:site_slug>/', SiteDetail.as_view(), name='site_detail'),
    path('site/edit/<slug:site_slug>/', SiteUpdate.as_view(), name='site_edit'),

    path('site/<slug:site_slug>edit-property/<str:property_type>/', UniversalPropertyView.as_view(), name='edit_property'),

    path('placement/<int:pk>/', PlacementDetailView.as_view(), name='placement-detail'),
    path('placement/edit/<int:pk>/', PlacementUpdateView.as_view(), name='placement-edit'),

    path('placement/new/', PlacementCreateView.as_view(), name='placement-create'),
    path('placements/', PlacementListView.as_view(), name='placement-list'),  # Make sure this line exists

    path('ajax/get_site_properties/<int:site_id>/<int:period_id>/', ajax_get_site_properties, name='get_site_properties'),
    # path('ajax/get_site_properties_/<int:site_id>/<int:period_id>/', get_site_properties, name='get_site_properties'),
    path('ajax/get_latest_ktg_for_car/<int:car_id>/<int:period_id>/', ajax_get_latest_ktg_for_car, name='get_latest_ktg_for_car'),

    path('ajax/get_cars_properties/', views.ajax_get_cars_properties, name='get_cars_properties'),

    path('ajax/get_cars_for_period/', views.get_cars_for_period, name='get_cars_for_period'),
    # path('ajax/get_cars_for_period/<int:site_id>/<int:period_id>/', views.get_cars_for_period, name='get_cars_for_period'),

    path('ajax/calc_placement/', views.calc_placement, name='calc_placement'),

]


