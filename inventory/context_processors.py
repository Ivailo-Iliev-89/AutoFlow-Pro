from .models import Client


def client_list_global(request):
    return {
        'all_clients_global': Client.objects.all().order_by('name')
    }
