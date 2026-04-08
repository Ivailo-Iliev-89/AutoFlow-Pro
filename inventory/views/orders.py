from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.template.loader import get_template
from django.http import HttpResponse
from django.db import transaction
from io import BytesIO
from xhtml2pdf import pisa
from decimal import Decimal
from inventory.models import Part, Client, Quotation, QuotationItem


def generate_pdf_quote(request):
    '''
    Generates a printable PDF document by calculating final prices and discounts.
    '''

    client_name = request.GET.get('client', 'Client')
    discount_val = Decimal(request.GET.get('discount', 0))
    items_raw = request.GET.get('items', '')

    parts_data = []
    subtotal = Decimal(0)

    if items_raw:
        item_pairs = items_raw.split(',')
        for pair in item_pairs:
            if ':' in pair:
                part_id, qty = pair.split(':')
                part = Part.objects.get(id=part_id)
                quantity = int(qty)
                line_total = part.sale_price * quantity

                parts_data.append({
                    'part': part,
                    'quantity': quantity,
                    'line_total': line_total
                })
                subtotal += line_total

    discount_amount = subtotal * (discount_val / Decimal(100))
    total = subtotal - discount_amount

    context = {
        'parts_data': parts_data,
        'client_name': client_name,
        'discount': float(discount_val),
        'subtotal': subtotal,
        'total': total,
    }

    template = get_template('inventory/pdf_template.html')
    html = template.render(context)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)

    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')

    return HttpResponse("Error generating PDF", status=400)


def reprint_pdf(request, quote_id):
    quote = get_object_or_404(Quotation, id=quote_id)
    items = quote.items.all()
    parts_data = []
    subtotal = Decimal('0.00')

    for item in items:
        line_total = item.curr_price * item.qty
        subtotal += line_total
        parts_data.append({
            'part': item.part,
            'quantity': item.qty,
            'line_total': line_total
        })

    discount_value = float(quote.discount_percent)

    context = {
        'parts_data': parts_data,
        'client_name': quote.client.name,
        'discount': discount_value,
        'subtotal': subtotal,
        'total': quote.total_price,
    }

    template = get_template('inventory/pdf_template.html')
    html = template.render(context)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)

    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return HttpResponse("Error generating PDF", status=400)


@login_required
@transaction.atomic
def finalize_quote(request):

    if not request.user.is_staff:
        client = request.user.client_profile
        discount = request.GET.get('discount', 0)
        items_raw = request.GET.get('items', '')
    else:
        client_id = request.GET.get('client_id')
        client = get_object_or_404(Client, id=client_id)
        discount = float(request.GET.get('discount', 0))
        items_raw = request.GET.get('items', '')

    new_quote = Quotation.objects.create(
        created_by=request.user,
        client=client,
        discount_percent=Decimal(str(discount))
    )

    grand_total = 0

    if items_raw:
        pairs = items_raw.split(',')
        for pair in pairs:
            if not pair:
                continue
            part_id, requested_qty = pair.split(':')
            part = get_object_or_404(Part, id=part_id)

            req_qty = int(requested_qty)
            actual_qty = min(req_qty, part.stock_qty)

            if actual_qty > 0:
                line_total = part.sale_price * actual_qty
                grand_total += line_total

                QuotationItem.objects.create(
                    quotation=new_quote,
                    part=part,
                    qty=actual_qty,
                    curr_price=part.sale_price,
                )

                part.stock_qty -= actual_qty
                part.save()

    discount_decimal = Decimal(str(discount))
    total_with_discount = Decimal(
        str(grand_total)) * (Decimal('1') - (discount_decimal / Decimal('100')))

    new_quote.total_price = total_with_discount
    new_quote.save()

    request.session['quote_list'] = []

    if request.user.is_staff:
        messages.success(request, f"Sale finalized for {client.name}!")
        return redirect('client_detail', pk=client.id)
    else:
        messages.success(request, "Your order has been successfully placed!")
        return redirect('dashboard')


@login_required
@transaction.atomic
def delete_quote(request, quote_id):
    quote = get_object_or_404(Quotation, id=quote_id)
    client_id = quote.client.id
    items = quote.items.all()

    for item in items:
        part = item.part
        part.stock_qty += item.qty
        part.save()

    quote.delete()

    messages.warning(
        request, f'Oferr #{quote_id} has been cancelled, and parts are succesfully returned to a Warehouse!')

    return redirect('client_detail', pk=client_id)
