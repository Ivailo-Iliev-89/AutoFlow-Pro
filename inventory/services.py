import json
from django.db.models import Sum
from django.db.models.functions import Coalesce, TruncMonth
from decimal import Decimal


def get_client_dashboard_data(user, quotations_queryset):
    """ Calculates all necessery stats and chart data for client"""

    # Basic Stats
    total_spent = quotations_queryset.aggregate(
        total=Coalesce(Sum('total_price'), Decimal('0.00'))
    )['total']

    order_count = quotations_queryset.count()

    # Monthly Grouping for Chart Logic
    order_by_month = quotations_queryset.annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        total=Sum('total_price')
    ).order_by('month')

    months = {
        1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr',
        5: 'May', 6: 'Jun', 7: 'July', 8: 'Aug',
        9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
    }

    chart_labels = []
    chart_data = []

    for entry in order_by_month:
        if entry['month']:
            label = f"{months[entry['month'].month]} {entry['month'].year}"
            chart_labels.append(label)
            chart_data.append(float(entry['total']))

    # User Initials (logged in as ...)
    if user.first_name and user.last_name:
        initials = f"{user.first_name[0]} {user.last_name[0]}".upper()
    else:
        initials = user.username[:2].upper()

    return {
        'total_spent': total_spent,
        'order_count': order_count,
        'chart_labels_json': json.dumps(chart_labels),
        'chart_data_json': json.dumps(chart_data),
        'initials': initials,
    }
