from django.db import models
from django.forms import ValidationError

# Create your models here.

PRODUCT_SUPPLEMENT_TYPES = (
    ('BUY', 'Покупка'),
    ('MANUFACTURE', 'Производство'),
    ('OTHER', 'Другое'),
)
PRODUCT_TYPES = (
    ('PRODUCT', 'Товар'),
    ('SEMI_PRODUCT', 'Полуфабрикат'),
    ('MATERIAL', 'Материал'),
    ('OTHER', 'Другое'),
)


# Main objects #
class MeasureUnit(models.Model):
    class Meta:
        verbose_name = 'Единица измерения'
        verbose_name_plural = 'Единицы измерения'
    name = models.CharField(unique=True, max_length=50)
    short = models.CharField(unique=True, max_length=10)


class Region(models.Model):
    class Meta:
        verbose_name = 'Регион'
        verbose_name_plural = 'Регионы'
    name = models.CharField(unique=True, max_length=200)
    code = models.CharField(unique=True, max_length=20)

    def __str__(self):
        if self.name:
            return self.name
        else:
            return self.code


def get_upload_url(instance, filename):
    if instance.pk:
        return 'uploads/%s/%s' % (instance.pk, filename)
    else:
        return 'uploads/%s' % filename


class Product(models.Model):
    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
    name = models.CharField()
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to=get_upload_url, null=True, blank=True)
    product_type = models.CharField(
        choices=PRODUCT_TYPES, default='OTHER', max_length=20)
    product_supplement_type = models.CharField(
        choices=PRODUCT_SUPPLEMENT_TYPES, default='OTHER', max_length=20)
    measure_unit = models.ForeignKey(
        MeasureUnit, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_values = models.JSONField(default=dict, blank=True)

    def save(self, *args, **kwargs):
        if self.pk:
            self.last_values = {
                'name': self.name,
                'description': self.description,
                'image': self.image,
                'product_type': self.product_type,
                'product_supplement_type': self.product_supplement_type,
            }
        super().save(*args, **kwargs)


class Storage(models.Model):
    class Meta:
        verbose_name = 'Склад'
        verbose_name_plural = 'Склады'
    name = models.CharField(unique=True, max_length=200)
    code = models.CharField(unique=True, max_length=20)
    region = models.ForeignKey(
        Region, related_name='storages', on_delete=models.CASCADE)

    description = models.TextField(blank=True)

    def __str__(self):
        if self.name:
            return self.name
        else:
            return self.code


class Barcode(models.Model):
    class Meta:
        verbose_name = 'Штрихкод'
        verbose_name_plural = 'Штрихкоды'
    name = models.CharField(max_length=100)
    product = models.ForeignKey(
        Product, related_name='barcodes', on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.name}'


class SalesPoint(models.Model):

    class Meta:
        verbose_name = 'Точка продаж'
        verbose_name_plural = 'Точки продаж'
    name = models.CharField(unique=True, max_length=255)
    code = models.CharField(unique=True, max_length=20)
    description = models.TextField(blank=True)


class Blueprint(models.Model):
    class Meta:
        verbose_name = 'Спецификация'
        verbose_name_plural = 'Спецификации'
    name = models.CharField(unique=True, max_length=255)
    product = models.ForeignKey(
        Product, related_name='blueprints', on_delete=models.CASCADE)
    barcode = models.ForeignKey(
        Barcode, related_name='blueprints', on_delete=models.SET_NULL, null=True)

    def save(self, *args, **kwargs):
        if self.barcode and self.barcode.product != self.product:
            raise ValidationError(
                'Barcode product must be the same as blueprint product')
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.name}'


class BlueprintItem(models.Model):
    class Meta:
        verbose_name = 'Элемент спецификации'
        verbose_name_plural = 'Элементы спецификации'
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    blueprint = models.ForeignKey(
        Blueprint, on_delete=models.SET_NULL, null=True)
    amount = models.IntegerField(default=1)
    owner_amount = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_value = models.JSONField(default=dict, blank=True)

    def save(self, *args, **kwargs):
        if self.blueprint:
            if self.product != self.blueprint.product:
                raise ValidationError(
                    'Product must be the same as blueprint product')
        if self.pk:
            self.last_value = {
                'product': self.product,
                'blueprint': self.blueprint,
                'amount': self.amount,
                'owner_amount': self.owner_amount,
            }
        super().save(*args, **kwargs)
