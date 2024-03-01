from django import forms
from django.contrib.auth.models import User
from django.forms.models import inlineformset_factory
from .models import Mine, Shaft, Car, YearMonth, Site, Plan_zadanie, Plotnost_gruza, Schema_otkatki, T_smeny, \
    T_regl_pereryv, T_pereezd, T_vspom, Nsmen, Ktg

PlanZadanieFormset = inlineformset_factory(Site, Plan_zadanie, fields='__all__', extra=1, can_delete=True)
Plotnost_gruzaFormset = inlineformset_factory(Site, Plotnost_gruza, fields='__all__', extra=1, can_delete=True)
Schema_otkatkiFormset   = inlineformset_factory(Site, Schema_otkatki, fields='__all__', extra=1, can_delete=True)
T_smenyFormset = inlineformset_factory(Site, T_smeny, fields='__all__', extra=1, can_delete=True)
T_regl_pereryvFormset = inlineformset_factory(Site, T_regl_pereryv, fields='__all__', extra=1, can_delete=True)
T_pereezdFormset = inlineformset_factory(Site, T_pereezd, fields='__all__', extra=1, can_delete=True)
T_vspomFormset = inlineformset_factory(Site, T_vspom, fields='__all__', extra=1, can_delete=True)
NsmenFormset = inlineformset_factory(Site, Nsmen, fields='__all__', extra=1, can_delete=True)


from django.forms.models import modelform_factory


class KtgForm(forms.ModelForm):
    class Meta:
        model = Ktg
        fields = ['KTG']
        labels = {'KTG': 'КТГ'}


def get_universal_property_form(model_class, initial_site=None,user=None,initial=None):
    # Создаем динамическую форму для данного класса модели.
    # UniversalPropertyForm = modelform_factory(model_class, fields='__all__')

    # UniversalPropertyForm = modelform_factory(model_class, exclude=('shaft', 'mine'))#, fields='__all__')

    # field_list = [field.name for field in model_class._meta.fields if field.name not in ('shaft', 'mine','created')]

    # UniversalPropertyForm = modelform_factory(model_class, fields=field_list)
    UniversalPropertyForm = modelform_factory(model_class, exclude = [('shaft', 'mine','created')])

    class CustomUniversalPropertyForm(UniversalPropertyForm):


        def __init__(self, *args, **kwargs):
            user = kwargs.pop('user', None)
            # super().__init__(*args, **kwargs)
            if initial is not None:
                kwargs['initial'] = initial
            super(CustomUniversalPropertyForm, self).__init__(*args, **kwargs)
            # Preselect the "changed_by" field to the current user
            if user is not None:
                self.fields['changed_by'].initial = user.id

                # If the user is an admin, provide a dropdown of all users
                if user.is_superuser:
                    self.fields['changed_by'] = forms.ModelChoiceField(queryset=User.objects.all(), initial=1)
                else:
                    # If not admin, make the field display only
                    self.fields['changed_by'].disabled = True
                    self.fields['changed_by'].help_text = "You cannot change this field."

            if initial_site:
                # Assuming 'site' is the field name in your form
                self.fields['site'].initial = initial_site
            # Dynamically add 'shaft' and 'mine' fields
            self.fields['shaft'] = forms.ModelChoiceField(
            # shaft = forms.ModelChoiceField(

                queryset=Shaft.objects.all(),
                required=False,
                empty_label="(опционально) Шахта целиком ",
                label="Шахта"
            )
            self.fields['mine'] = forms.ModelChoiceField(
            # mine = forms.ModelChoiceField(

                queryset=Mine.objects.all(),
                required=False,
                empty_label="(опционально) Рудник целиком ",
                label="Рудник"
            )


    return CustomUniversalPropertyForm


class UniversalPropertyForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        model_class = kwargs.pop('model_class', None)
        super().__init__(*args, **kwargs)
        if model_class:
            self._meta.model = model_class


class AddPostForm(forms.ModelForm):
    class Meta:
        model = Car
        fields = '__all__'


class UploadFilesForm(forms.Form):
    file = forms.ImageField(label='Файл')


class SiteEditForm(forms.ModelForm):
    plan_zadanie_qpl = forms.FloatField(required=False)
    plan_zadanie_period = forms.ModelChoiceField(
        queryset=YearMonth.objects.all(),
        required=False,
        empty_label="Выбрать период",
        label="Период"
    )
    class Meta:
        model = Site
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(SiteEditForm, self).__init__(*args, **kwargs)
        if self.instance:
            latest_plan_zadanie = self.instance.plan_zadanie.order_by('-created').first()
            if latest_plan_zadanie:
                self.fields['plan_zadanie_qpl'].initial = latest_plan_zadanie.Qpl
                self.fields['plan_zadanie_period'].initial = latest_plan_zadanie.period
            else:
                self.fields['plan_zadanie_qpl'].initial = None
                self.fields['plan_zadanie_period'].initial = None

    def save(self, commit=True, user=None):
        instance = super(SiteEditForm, self).save(commit=False)
        qpl = self.cleaned_data.get('plan_zadanie_qpl')
        period = self.cleaned_data.get('plan_zadanie_period')  # This is a YearMonth instance

        if commit:
            instance.save()

            new_plan_zadanie = Plan_zadanie.objects.create(
                Qpl=qpl,
                period=period,
                site=instance,
                changed_by=user,
            )

        return instance



class PropertyEditForm(forms.ModelForm):
    class Meta:
        model = None  # We will specify the model dynamically
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        model_class = kwargs.pop('model_class', None)
        super().__init__(*args, **kwargs)
        if model_class:
            self._meta.model = model_class
            self.fields = model_class._meta.get_fields()