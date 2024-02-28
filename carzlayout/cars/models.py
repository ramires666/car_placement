from django.conf import settings
from django.db import models
from django.urls import reverse
# from django.utils.text import slugify
from pytils.translit import slugify
import reversion
from simple_history.models import HistoricalRecords





@reversion.register()
class Mine(models.Model):
    title = models.CharField(max_length=255, verbose_name='Рудник')
    slug = models.SlugField(null=True, unique=False, blank=True)
    history = HistoricalRecords()

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        # super(Mine, self).save(*args, **kwargs)
        super(Mine, self).save(*args, **kwargs)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Рудник"
        verbose_name_plural = "Рудники"


@reversion.register()
class Shaft(models.Model):
    title = models.CharField(max_length=255, verbose_name='Шахта')
    mine = models.ForeignKey(Mine,on_delete=models.DO_NOTHING,null=True)
    slug = models.SlugField(null=True, unique=False, blank=True)
    history = HistoricalRecords()
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f'{self.mine.slug}-{self.title}')
        super(Shaft, self).save(*args, **kwargs)

    def __str__(self):
        return self.title+" "+self.mine.title

    class Meta:
        verbose_name = "Шахта"
        verbose_name_plural = "Шахты"




class Site(models.Model):
    title = models.CharField(max_length=255, verbose_name='Участок')
    # year_month = models.ForeignKey(YearMonth,on_delete=models.DO_NOTHING)
    shaft = models.ForeignKey(Shaft, on_delete=models.DO_NOTHING,null=True)
    slug = models.SlugField(null=True, unique=False, blank=True)
    history = HistoricalRecords()

    # @property
    # def plan_zadanie(self):
    #     try:
    #         # return self.plan_zadanie.Qpl
    #         return Plan_zadanie.objects.filter(site=self).order_by('-created')  # Assuming 'created' is a timestamp field in Plan_zadanie
    #     except Plan_zadanie.DoesNotExist:
    #         return None

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f'{self.shaft.slug}-{self.title}')
        super(Site, self).save(*args, **kwargs)

    def __str__(self):
        return self.title+" "+self.shaft.title

    class Meta:
        verbose_name = "Участок"
        verbose_name_plural = "Участки"




class YearMonth(models.Model):
    title = models.CharField(max_length=255, blank=True)
    year = models.IntegerField(default=2024)
    # month = models.IntegerField(default=0)
    class Month(models.IntegerChoices):
        year = 0, 'Год'
        jan = 1, 'Январь'
        feb = 2, 'Февраль'
        mar = 3, 'Март'
        apr = 4, 'Апрель'
        may = 5, 'Май'
        jun = 6, 'Июнь'
        jul = 7, 'Июль'
        aug = 8, 'Август'
        sep = 9, 'Сентябрь'
        oct = 10, 'Октябрь'
        nov = 11, 'Ноябрь'
        dec = 12, 'Декабрь'
    month = models.IntegerField(choices=tuple(map(lambda x: (int(x[0]),x[1]),Month.choices)),default=Month.year)
    history = HistoricalRecords()

    def __str__(self):
        return f"{self.year}-{self.get_month_display()}"#self.title

    def save(self, *args, **kwargs):
        # Automatically set the title field based on year and month
        self.title = f"{self.year}-{self.get_month_display()}"
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Период"
        verbose_name_plural = "Периоды"



class PropertyBase(models.Model):
    period = models.ForeignKey(YearMonth,on_delete=models.PROTECT,verbose_name="Период")
    site = models.ForeignKey(Site, on_delete=models.CASCADE,verbose_name="Участок")
    created = models.DateTimeField(auto_now_add=True,verbose_name="Дата_обновления")
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,verbose_name="Автор")
    document = models.FileField(upload_to='property_documents/', null=True, blank=False,verbose_name="Документ_обоснование")
    history = HistoricalRecords()
    class Meta:
        abstract = True


class Plan_zadanie(PropertyBase):
    Qpl = models.FloatField(verbose_name="План задание")

    class Meta:
        verbose_name="Qpl - План задание"



class Plotnost_gruza(PropertyBase):
    d = models.FloatField(verbose_name="Плотность груза")
    class Meta:
        verbose_name="d - Плотность груза"



class Schema_otkatki(PropertyBase):
    L = models.FloatField(verbose_name="Плечо откатки")
    class Meta:
        verbose_name="L - Плечо откатки"




class T_smeny(PropertyBase):
    Tsm = models.FloatField(verbose_name="Длительность смены")
    class Meta:
        verbose_name="Tsm - Длительность смены"




class T_regl_pereryv(PropertyBase):
    Tregl = models.FloatField(verbose_name="Регламентные перерывы")
    class Meta:
        verbose_name="Tregl - Регламентные перерывы"




class T_pereezd(PropertyBase):
    Tprz = models.FloatField(verbose_name="Время переезда")
    class Meta:
        verbose_name="Tprz - Время переезда"




class T_vspom(PropertyBase):
    Tvsp = models.FloatField(verbose_name="Вспомогательное время")
    class Meta:
        verbose_name="Tvsp - Вспомогательное время"




class Nsmen(PropertyBase):
    Nsm = models.FloatField(verbose_name="Количество смен")
    class Meta:
        verbose_name="Nsm - Количество смен"


class V_objem_kuzova(PropertyBase):
    Vk = models.FloatField(verbose_name="Объем кузова")
    class Meta:
        verbose_name="Vk - Объем кузова"


class Kuzov_Coeff_Zapl(PropertyBase):
    Kz = models.FloatField(verbose_name="Коэффициент заполнения кузова")
    class Meta:
        verbose_name="Kz - Коэффициент заполнения кузова"


class V_Skorost_dvizh(PropertyBase):
    Vdv = models.FloatField(verbose_name="Средн. скорость движения")
    class Meta:
        verbose_name="Vdv - Средн. скорость движения"



class T_pogruzki(PropertyBase):
    Tpogr = models.FloatField(verbose_name="Продолжит погрузки со сменой автосам")
    class Meta:
        verbose_name="Tpogr - Продолжит погрузки со сменой автосам"


class T_razgruzki(PropertyBase):
    Trazgr = models.FloatField(verbose_name="Прожолжит. разгрузки с маневрами")
    class Meta:
        verbose_name="Trazgr - Прожолжит. разгрузки с маневрами"





class PublishedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_published=Car.Status.PUBLISHED)


@reversion.register()
class Car(models.Model):
    class Status(models.IntegerChoices):
        DRAFT = 0, 'Черновик'
        PUBLISHED = 1, 'Опубликовано'

    title = models.CharField(max_length=255, verbose_name='Название')
    # KTG = models.FloatField(blank=True,null=True,verbose_name='КТГ')
    V_objem_kuzova = models.FloatField(blank=True, null=True, verbose_name='Емкость кузова с шапкой')
    slug = models.SlugField(max_length=255,unique=True, db_index=True)
    photo = models.ImageField(upload_to='photos/%Y/%m/%d/',default=None,blank=True,null=True,verbose_name='Фоточка')
    content = models.TextField(blank=True,verbose_name="Описание")
    time_create = models.DateTimeField(auto_now_add=True)
    time_update = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(choices=tuple(map(lambda x: (bool(x[0]),x[1]), Status.choices)), default=Status.DRAFT)
    cat = models.ForeignKey('Category', on_delete=models.PROTECT, related_name='cars',verbose_name='Категория')
    tags = models.ManyToManyField('TagPost',blank=True,related_name='tags')
    history = HistoricalRecords()

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Машина"
        verbose_name_plural = "Машины"
        ordering =['-time_create']
        indexes = [models.Index(fields=['-time_create'])]

    def get_absolute_url(self):
        return reverse('car', kwargs={'car_slug': self.slug})



    # class PublishedModel(models.Manager):
    #     def get_queryset(self):
    #         return super().get_queryset().filter(is_published=1)

    objects = models.Manager()
    published = PublishedManager()


class CarPropertyBase(models.Model):
    period = models.ForeignKey(YearMonth,on_delete=models.PROTECT,verbose_name="Период")
    # site = models.ForeignKey(Site, on_delete=models.CASCADE,verbose_name="Участок")
    created = models.DateTimeField(auto_now_add=True,verbose_name="Дата_обновления")
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,verbose_name="Автор")
    document = models.FileField(upload_to='property_documents/', null=True, blank=False,verbose_name="Документ_обоснование")
    history = HistoricalRecords()
    class Meta:
        abstract = True


class Ktg(CarPropertyBase):
    KTG = models.FloatField(verbose_name="КТГ")
    class Meta:
        verbose_name="KTG - КТГ"


@reversion.register()
class Category(models.Model):
    name = models.CharField(max_length=100, db_index=True, verbose_name="Категория")
    slug = models.SlugField(max_length=255, unique=True, db_index=True)
    objects = models.Manager()
    history = HistoricalRecords()
    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('category', kwargs={'cat_slug':self.slug})

class TagPost(models.Model):
    tag = models.CharField(max_length=100, db_index=True)
    slug = models.SlugField(max_length=255, unique=True, db_index=True)
    def __str__(self):
        return self.tag

    def get_absolute_url(self):
        return reverse('tag', kwargs={'tag_slug':self.slug})


@reversion.register()
class UploadFiles(models.Model):
    file = models.FileField(upload_to='uploads_model')
    history = HistoricalRecords()