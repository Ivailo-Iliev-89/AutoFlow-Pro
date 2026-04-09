from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.db.models import Q, Sum
from inventory.models import Part, Client


@login_required
def part_list(request):
    """
    Find parts and show warehouse stats, AJAX requests for real-time searching
    """
    query = request.GET.get('q', '')

    if query:
        parts = Part.objects.filter(
            Q(name__icontains=query) |
            Q(oem_num__icontains=query) |
            Q(brand__name__icontains=query)
        )
    else:
        parts = Part.objects.none()

    total_parts_count = Part.objects.count()
    total_stock_qty = Part.objects.aggregate(
        total=Sum('stock_qty'))['total'] or 0
    critical_parts = Part.objects.filter(stock_qty__lt=3)[:5]
    recent_parts = Part.objects.all().order_by('-id')[:5]

    context = {
        'parts': parts,
        'query': query,
        'total_parts_count': total_parts_count,
        'total_stock_qty': total_stock_qty,
        'critical_parts': critical_parts,
        'recent_parts': recent_parts
    }

    # AJAX Logic
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html = render_to_string(
            'inventory/includes/part_table_partial.html', {'parts': parts})
        return JsonResponse({'html': html})

    return render(request, 'inventory/part_list.html', context)


def add_to_quote(request, part_id):
    '''
    Adds a unique part ID to the session list (shop-cart) without reloading the page.
    '''

    quote_list = request.session.get('quote_list', [])

    if part_id not in quote_list:
        quote_list.append(part_id)
    request.session['quote_list'] = quote_list

    return JsonResponse({'status': 'ok', 'count': len(quote_list)})


@login_required
def view_quote(request):
    """
    Prepare data for Shop-Cart, collect selected parts and check which user is and what kind of discount have
    """
    quote_list = request.session.get('quote_list', [])
    parts = Part.objects.filter(id__in=quote_list)

    clients = None
    current_client_discount = 0

    if request.user.is_staff:  # Admin Logic
        clients = Client.objects.all().order_by('name')
        current_client_discount = 0
    else:  # Customer Logic
        client_profile = getattr(request.user, 'client_profile', None)

        if client_profile:
            current_client_discount = client_profile.def_discount
        else:
            current_client_discount = 0

    # Calculate price without discount
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
