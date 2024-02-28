from .models import Plan_zadanie, Plotnost_gruza, Schema_otkatki, T_smeny, T_regl_pereryv, T_pereezd, T_vspom, Nsmen
from django.conf import settings
from django.db.models import Model
from typing import Type
from django.forms.models import inlineformset_factory
from django.utils.safestring import mark_safe


from django.db.models import Max,Min
from django.urls import reverse

def generate_edit_url(self, property_key, site_id):
    """
    Генерирует URL для универсального представления редактирования свойства участка.

    Args:
    - property_key: ключ свойства, для которого генерируется URL.
    - site_id: идентификатор участка.

    Returns:
    - Строка с URL.
    """
    return reverse('edit_property', kwargs={'property_type': property_key, 'site_id': site_id})


class SiteDataService:
    def __init__(self, site):
        self.site = site

    def get_all_data(self):
        models_to_fetch = {
            'plan_zadanie': Plan_zadanie,
            'plotnost_gruza': Plotnost_gruza,
            'schema_otkatki': Schema_otkatki,
            't_smeny': T_smeny,
            't_regl_pereryv': T_regl_pereryv,
            't_pereezd': T_pereezd,
            't_vspom': T_vspom,
            'nsmen': Nsmen,

        }

        data = {}
        for key, model in models_to_fetch.items():
            full_data = self._get_related_model_data(model)
            filtered_data = self._get_filtered_model_data(model)
            data[key] = {
                'full': full_data,
                'filtered': filtered_data,
            }
        return data

    def _get_related_model_data(self, model):
        records = model.objects.filter(site=self.site).order_by('-created')
        return self._format_records(records)

    def _get_filtered_model_data(self, model):
        # Fetch the latest record for each YearMonth period
        latest_records_ids = model.objects.filter(site=self.site) \
            .values('period') \
            .annotate(latest_id=Max('id')) \
            .values_list('latest_id', flat=True)

        latest_records = model.objects.filter(id__in=latest_records_ids).order_by('period__year', 'period__month')
        return self._format_records(latest_records)

    def _format_records(self, records):
        formatted_records = []
        for record in records:
            formatted_record = {
                'Период': f"{record.period.year}-{record.period.get_month_display()}",
                'Создано': record.created.strftime("%Y-%m-%d %H:%M"),
                'Изменил': record.changed_by.username if record.changed_by else 'N/A',
            }
            # Add model-specific fields dynamically
            for field in record._meta.fields:
                if field.name in ['id', 'site', 'period', 'created', 'changed_by']:
                    continue  # Skip these fields
                if field.name == 'document' and getattr(record, field.name):
                    document_url = getattr(record, field.name).url
                    link_html = f'<a href="javascript:void(0)" onclick="showImageModal(\'{document_url}\')">Open Document</a>'
                    formatted_record[field.verbose_name] = mark_safe(link_html)
                else:
                    formatted_record[field.verbose_name] = getattr(record, field.name, '')
            formatted_records.append(formatted_record)
        return formatted_records


