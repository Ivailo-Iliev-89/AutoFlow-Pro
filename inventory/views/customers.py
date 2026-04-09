from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum
from django.db.models.functions import Coalesce
from decimal import Decimal
from inventory.models import Part, Client, Quotation
from inventory.forms import CustomUserCreationForm
from ..services import get_client_dashboard_data


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

        else:  # CUSTOMER LOGIC

            # Filter by 'client__user' to reach the User model through the Client
            try:
                client_profile = request.user.client_profile
                my_orders = Quotation.objects.filter(
                    client=client_profile).order_by('-created_at')

            # If the client relation fails, filter by the creator of the record
            except:
                client_profile = None
                my_orders = Quotation.objects.filter(
                    created_by=request.user).order_by('-created_at')

            stats = get_client_dashboard_data(request.user, my_orders)

            context = {
                'client': client_profile,
                'my_orders': my_orders[:10],
                **stats
            }

            return render(request, 'clients/client_dashboard.html', context)

    return render(request, 'inventory/landing_page.html', {})


def client_list(request):
    '''
    Displays a list of all registered customers in the system (Stores, Services, Individuals).
    '''

    clients = Client.objects.all().order_by('name')

    return render(request, 'clients/client_list.html', {'clients': clients})


def client_detail(request, pk):
    '''
    Displays Customer profile - Contact information and history of sales.
    '''

    client = get_object_or_404(Client, pk=pk)
    client_quotations = client.quotations.all().order_by(
        '-created_at')[:5]

    # Calculate total turnover to current client for all offers
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
