from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings


# Car (VW, BMW)
class Carmake(models.Model):
    name = models.CharField(max_length=50, verbose_name='Car brand')

    def __str__(self):
        return self.name


# Car Model (Golf 4, E46)
class CarModel(models.Model):

    make = models.ForeignKey(
        Carmake, on_delete=models.CASCADE, related_name='models')
    name = models.CharField(max_length=100, verbose_name='Model')
    year_from = models.IntegerField(verbose_name='Year From')
    year_to = models.IntegerField(
        null=True, blank=True, verbose_name='Year To')

    def __str__(self):
        return f'{self.make.name} {self.name} ({self.year_from} - {self.year_to})'


# Users
class User(AbstractUser):

    is_warehouse_manager = models.BooleanField(default=False)
    is_sales_rep = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=15, blank=True)


# Parts Manufacturers (TRW, Lemforder)
class Brand(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


# Part Catalog
class Part(models.Model):

    oem_num = models.CharField(max_length=50, unique=True)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_qty = models.IntegerField(default=0)
    category = models.ForeignKey(
        'Category', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f'{self.oem_num} - {self.name}'


# Clients
class Client(models.Model):

    CLIENT_TYPES = (
        ('service', 'Car service'),
        ('retail', 'Individuals'),
        ('shop', 'Auto Parts Shop')
    )

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name='client_profile', null=True, blank=True)
    name = models.CharField(max_length=200, verbose_name='Name/Company')
    email = models.EmailField(blank=True)
    adress = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    client_type = models.CharField(
        max_length=10, choices=CLIENT_TYPES, default='retail')
    def_discount = models.DecimalField(
        max_digits=5, decimal_places=2, default=10)

    def __str__(self):
        return f'{self.name} ({self.get_client_type_display()})'


# Part Categories
class Category(models.Model):

    name = models.CharField(max_length=100, verbose_name='Category')
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name


# Main Offer Document --> Who made the offer, who it is for and what is the total amount
class Quotation(models.Model):

    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    client = models.ForeignKey(
        Client, on_delete=models.SET_NULL, null=True, related_name='quotations')
    client_name = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    discount_percent = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00)
    total_price = models.DecimalField(
        max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f'{self.id} - {self.client_name}'


# Historical Data - Keep the part price it was given
class QuotationItem(models.Model):

    quotation = models.ForeignKey(
        Quotation, on_delete=models.CASCADE, related_name='items')
    part = models.ForeignKey(Part, on_delete=models.CASCADE)
    qty = models.PositiveBigIntegerField(default=1)
    curr_price = models.DecimalField(max_digits=10, decimal_places=2)
