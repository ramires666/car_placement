from django import template

register = template.Library()

@register.filter(name='rus_verbose')
def verbose_russian(name):
    names = {
        'plan_zadanie': 'План задание',
        'plotnost_gruza': 'Плотность груза',
        'schema_otkatki': 'Плечо откатки',
        't_smeny': 'Длина смены',
        't_regl_pereryv': 'Регламентные перерывы',
        't_pereezd': 'Время переезда',
        't_vspom': 'Вспомогательное время',
        'nsmen': 'Количество смен'
    }
    return names.get(name)


@register.filter(name='trim_suffix')
def trim_suffix(value, suffix):
    if isinstance(value, str) and value.endswith(suffix):
        return value[:-len(suffix)]
