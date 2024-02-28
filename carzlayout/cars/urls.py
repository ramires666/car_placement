from django.urls import path, re_path, register_converter
from cars import views
from cars.views import CarsHome, SiteDetail, SiteUpdate, edit_property_view, UniversalPropertyView

from cars import converter
register_converter(converter.FourDigitYearConverter,'year4')


urlpatterns = [
    # path('',views.index, name='home'),
    path('', CarsHome.as_view(), name='home'),
    path('about/',views.about, name='about'),
    # path('cars/',views.cars,name='cars'),
    path('cars/<int:car_id>/', views.cars,name='car_id'),
    path('cars/<slug:car_slug>/', views.cars_by_producer,name='cars_by_producer'),
    # re_path(r"^archive/(?P<year>[0-9]{4})/", views.archive)
    path('archive/<year4:year>/', views.archive,name='archive'),

    path('add_page/', views.add_page, name='add_page'),
    path('contact/', views.contact, name='contact'),
    path('login/', views.login, name='login'),

    path('post/<slug:post_slug>/', views.show_post, name='post'),

    # path('post/<int:post_id>/', views.show_post, name='post'),
    path('category/<slug:cat_slug>/', views.show_category, name='category'),
    path('tag/<slug:tag_slug>/', views.show_tag_postlist, name='tag'),

    path('mines/', views.mines_list, name='mines_list'),
    path('mines/<slug:mine_slug>/', views.shafts_list, name='shafts_list'),
    path('shafts/<slug:shaft_slug>/', views.sites_list, name='sites_list'),
    # re_path(r'mines/(?P<mine_slug>[\w-]+)/$', views.shafts_list, name='shaft_list'),
    path('places/',views.places, name='places'),
    path('mine/<slug:mine_slug>/', views.mine_detail, name='mine_detail'),
    path('shaft/<slug:shaft_slug>/', views.shaft_detail, name='shaft_detail'),
    # path('site/<slug:site_slug>/', views.site_detail, name='site_detail'),
    path('site/<slug:site_slug>/', SiteDetail.as_view(), name='site_detail'),
    path('site/edit/<slug:site_slug>/', SiteUpdate.as_view(), name='site_edit'),
    # path('site/<int:site_id>/edit/<str:model_name>/<int:property_id>/', edit_property, name='edit_property'),
    # path('site/<slug:site_slug>/edit/<str:model_name>/<int:property_id>/', EditPropertyView.as_view(), name='edit_property'),
    # path('site/<slug:site_slug>/edit-property/<str:model_name>/<int:property_id>/', edit_property_view,
    #      name='edit_property'),
    path('site/<slug:site_slug>/edit-property/<str:property_type>/', UniversalPropertyView.as_view(), name='edit_property'),

]


