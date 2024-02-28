from django import template
import cars.views as views
from cars.models import Category, TagPost

register  = template.Library()

@register.simple_tag
def get_menu():
    return views.menu

@register.inclusion_tag('cars/list_categories.html')
def show_categories(cat_selected=0):
    cats = Category.objects.all()
    return {'cats': cats, 'cat_selected':cat_selected}


@register.inclusion_tag('cars/list_tags.html')
def show_all_tags():
    tags = TagPost.objects.all()
    return {'tags': tags}