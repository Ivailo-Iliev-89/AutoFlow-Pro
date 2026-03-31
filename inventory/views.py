from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.template.loader import get_template, render_to_string
from django.http import JsonResponse, HttpResponse
from django.db import transaction
from django.db.models import Q, Sum
from django.db.models.functions import Coalesce
from io import BytesIO
from xhtml2pdf import pisa
from decimal import Decimal
from .models import Part, Client, Quotation, QuotationItem
from .forms import CustomUserCreationForm


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
def part_list(request):

    query = request.GET.get('q', '')

    if query:
        parts = Part.objects.filter(
            Q(name__icontains=query) |
            Q(oem_num__icontains=query) |
            Q(brand__name__icontains=query)
        )
    else:
        parts = Part.objects.none()

    context = {
        'parts': parts,
        'query': query,
        'total_parts_count': Part.objects.count(),
        'total_stock_qty': Part.objects.aggregate(total=Sum('stock_qty'))['total'] or 0,
        'critical_parts': Part.objects.filter(stock_qty__lt=3)[:5],
        'recent_parts': Part.objects.all().order_by('-id')[:5]
    }
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html = render_to_string(
            'inventory/includes/part_table_partial.html', {'parts': parts})
        return JsonResponse({'html': html})

    return render(request, 'inventory/part_list.html', context)


def add_to_quote(request, part_id):
    '''
    Adds a unique part ID to the session list (cart) without reloading the page.
    '''

    quote_list = request.session.get('quote_list', [])

    if part_id not in quote_list:
        quote_list.append(part_id)
    request.session['quote_list'] = quote_list

    return JsonResponse({'status': 'ok', 'count': len(quote_list)})


@login_required
def view_quote(request):
    quote_list = request.session.get('quote_list', [])
    parts = Part.objects.filter(id__in=quote_list)

    clients = None
    current_client_discount = 0

    if request.user.is_staff:
        clients = Client.objects.all().order_by('name')
        current_client_discount = 0
    else:
        client_profile = getattr(request.user, 'client_profile', None)

        if client_profile:
            current_client_discount = client_profile.def_discount
        else:
            current_client_discount = 0

    total = sum(part.sale_price for part in parts)

    return render(request, 'inventory/quote_detail.html', {
        'parts': parts,
        'total': total,
        'clients': clients,
        'current_client_discount': current_client_discount,
    })


def clear_quote(request):
    '''
    Deletes the entire parts list from the current session and returns the user to the warehouse.
    '''

    if 'quote_list' in request.session:
        del request.session['quote_list']

    return redirect('part_list')


def remove_from_quote(request, part_id):
    '''
    Removes a specific part of the offer by filtering the list in the session by ID
    '''

    quote_list = request.session.get('quote_list', [])

    # ID in session it could be int or str --> it make it a str
    part_id_as_str = str(part_id)

    if part_id_as_str in [str(id) for id in quote_list]:
        # List without current ID
        new_list = [id for id in quote_list if str(id) != part_id_as_str]
        request.session['quote_list'] = new_list
        request.session.modified = True

    return redirect('view_quote')


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


def client_list(request):
    '''
    Displays a list of all registered customers in the system (Stores, Services, Individuals).
    '''

    clients = Client.objects.all().order_by('name')

    return render(request, 'clients/client_list.html', {'clients': clients})


def dashboard(request):
    if request.user.is_authenticated:

        if request.user.is_staff:
            total_sales = Quotation.objects.aggregate(
                total=Coalesce(Sum('total_price'), Decimal('0.00')))['total']
            total_clients_count = Client.objects.count()
            recent_quotes = Quotation.objects.select_related(
                'client').filter(client__isnull=False).order_by('-created_at')[:5]
            total_parts = Part.objects.count()

            context = {
                'total_sales': total_sales,
                'total_clients': total_clients_count,
                'recent_quotes': recent_quotes,
                'total_parts': total_parts,
            }
            return render(request, 'inventory/registration/admin_dashboard.html', context)

        else:
            my_orders = Quotation.objects.filter(
                created_by=request.user).order_by('-created_at')
            total_spent = my_orders.aggregate(total=Coalesce(
                Sum('total_price'), Decimal('0.00')))['total']

            context = {
                'my_orders': my_orders[:10],
                'total_spent': total_spent,
                'order_count': my_orders.count(),
            }

            return render(request, 'clients/client_dashboard.html', context)

    return render(request, 'inventory/landing_page.html', {})


def client_detail(request, pk):
    '''
    Displays Customer profile - Contact information and history of sales.
    '''
    client = get_object_or_404(Client, pk=pk)
    client_quotations = client.quotations.all().order_by(
        '-created_at')[:5]  # Shows last 5 offers

    # Calculate total turnover for curr client for all offers
    total_spent = sum(q.total_price for q in client_quotations.all())

    context = {
        'client': client,
        'quotations': client_quotations,
        'total_spent': total_spent,
    }

    return render(request, 'clients/client_detail.html', context)


def register(request):
    if request.method == 'POST':

        form = CustomUserCreationForm(request.POST)

        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            email = form.cleaned_data.get('email')

            Client.objects.create(
                user=user,
                name=username,
                email=email,
                def_discount=10,
            )

            messages.success(
                request, f'Account created for {username}! You can now log in.')
            return redirect('login')
    else:
        form = CustomUserCreationForm()

    return render(request, 'inventory/registration/register.html', {'form': form})


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
