from django.contrib import admin
from .models import Brand, Carmake, CarModel, Part, User, Category, Client, Quotation, QuotationItem


admin.site.register(Carmake)
admin.site.register(CarModel)
admin.site.register(Brand)
admin.site.register(User)
admin.site.register(Category)
admin.site.register(Client)


class QuotationItemInline(admin.TabularInline):
    model = QuotationItem
    extra = 0
    readonly_fields = ('part', 'qty', 'curr_price')


@admin.register(Quotation)
class QuotationAdmin(admin.ModelAdmin):

    list_display = ('id', 'client', 'discount_percent',
                    'total_price', 'created_at', 'created_by')
    list_filter = ('created_at', 'client', 'created_by')
    search_fields = ('client__name', 'id')
    inlines = [QuotationItemInline]
    ordering = ('-created_at',)


@admin.register(Part)
class PartAdmin(admin.ModelAdmin):
    list_display = ('oem_num', 'brand', 'name', 'sale_price', 'stock_qty')
    search_fields = ('oem_num', 'name')
    list_filter = ('brand', 'category')
