from django.shortcuts import render, redirect
from .models import *
from django.contrib.auth import login
from .forms import UserRegistrationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login,logout
from django.contrib import messages

import json
from decimal import Decimal
from django.http import JsonResponse
from django.db import transaction
from django.views.decorators.http import require_POST

# ... (your other models)
from .models import Table, MenuItem, Bill

from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
# from .models import Bill, BillItem
# from decimal import Decimal

from django.contrib import messages

# ... (other imports)
from django.db import transaction
from django.views.decorators.http import require_POST

# MODIFY THIS LINE to include Kot
# from .models import Table, MenuItem, Bill, BillItem, Kot

from django.shortcuts import render, redirect
from .models import *
from django.contrib.auth import login
from .forms import UserRegistrationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login,logout
from django.contrib import messages

import logging # <-- ADD THIS LINE
from django.db.models import Max 
# ... (all your other imports)
# --- NEW VIEWS FOR KOT (Kitchen Order Token) ---
# Get an instance of a logger
logger = logging.getLogger(__name__)

# Create your views here.

@login_required(login_url='login')
def index_view(request):
    # Fetch table data (as before)
    table_categories = TableCategory.objects.prefetch_related('table_set').all()
    
    # Fetch all menu categories and their associated menu items efficiently
    menu_categories = MenuCategory.objects.prefetch_related('menuitem_set').all()
    

    data_objects = Table.objects.all()  # Retrieve all objects from MyModel
    
    # bill = Bill.objects.all()
    last_bill = Bill.objects.order_by('-id').first() # Get the most recent bill
    last_bill_id = last_bill.id if last_bill else None # Get ID or None

    
    context = {
        'table_categories': table_categories,
        'menu_categories': menu_categories,
        'user': request.user,
        'data_objects': data_objects,
        'last_bill_id': last_bill_id
        
    }


    
    return render(request, 'index.html', context)


def logout_view(request):
    logout(request)
    return redirect('login')



def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('index')
        else:
            messages.error(request, 'Invalid username or password')
            return render(request, 'registration/login.html')
    return render(request, 'registration/login.html')

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            # UserCreationForm already hashes password on save(), but since you changed
            # to commit=False, set_password then save:
            user.set_password(form.cleaned_data['password1'])
            user.save()
            # authenticate then login
            user = authenticate(username=user.username, password=form.cleaned_data['password1'])
            if user:
                login(request, user)
                return redirect('index')
            return redirect('registration/login')
        else:
            # show form errors on page
            messages.error(request, 'Please enter same password in both fields.')
    else:
        form = UserRegistrationForm()
    return render(request, 'registration/register.html', {'form': form})


@require_POST  # Ensures this view only accepts POST requests
@transaction.atomic  # Ensures the bill is only saved if all items are saved
def save_bill_view(request):
    try:
        # Load the JSON data sent from the JavaScript
        data = json.loads(request.body)

        table_id = data.get('table_id')
        table_name = data.get('table_name')
        payment_method = data.get('payment_method')
        total_amount = Decimal(data.get('total_amount'))
        items = data.get('items', [])

        # Find the table object
        try:
            table = Table.objects.get(id=table_id)
        except Table.DoesNotExist:
            table = None # Or you could return an error

        # 1. Create the main Bill object
        new_bill = Bill.objects.create(
            table=table,
            table_name=table_name,
            total_amount=total_amount,
            payment_method=payment_method
        )

        # 2. Create the BillItem objects for each item in the order
        for item_data in items:
            try:
                # Find the original menu item
                menu_item = MenuItem.objects.get(id=item_data.get('id'))
            except MenuItem.DoesNotExist:
                menu_item = None # Item might have been deleted, still record the sale

            BillItem.objects.create(
                bill=new_bill,
                menu_item=menu_item,
                item_name=item_data.get('name'),
                quantity=item_data.get('qty'),
                price=Decimal(item_data.get('price'))
            )
        
        # If everything is successful, return a success response
        return JsonResponse({'success': True, 'bill_id': new_bill.id})

    except Exception as e:
        # If any error occurs, return an error response
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    


def print_bill_view(request, bill_id):
    try:
        # Get the bill and its related items
        bill = Bill.objects.get(id=bill_id)
        items = bill.items.all() # This uses the 'related_name' from your BillItem model

        # Add total price per item for the template
        items_with_totals = []
        for item in items:
            item.total_item_price = item.price * item.quantity
            items_with_totals.append(item)

        # Context for the template 
        context = {
            'bill': bill,
            'items': items_with_totals
        }

        # Render the HTML template to a string
        # html_string = render_to_string('index.html', context)
        html_string = render_to_string('bill_templates.html', context)

        # Generate PDF
        pdf_file = HTML(string=html_string, base_url=None).write_pdf()

        # Create an HTTP response with the PDF
        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="bill_{bill_id}.pdf"'
        return response

    except Bill.DoesNotExist:
        return HttpResponse("Bill not found.", status=404)
    except Exception as e:
        return HttpResponse(f"Error generating PDF: {e}", status=500)
    



@require_POST
@transaction.atomic
def create_kot_view(request):
    try:
        data = json.loads(request.body)
        
        table_id = data.get('table_id')
        table_name = data.get('table_name')
        items = data.get('items', [])

        if not items:
            return JsonResponse({'success': False, 'error': 'Cannot print an empty KOT.'}, status=400)

        # Find the table object
        try:
            table = Table.objects.get(id=table_id)
        except Table.DoesNotExist:
            table = None

        # --- Generate new numeric KOT ID ---
        logger.info("KOT CREATE: Attempting to generate new KOT ID.")
        last_kot = Kot.objects.aggregate(max_id=Max('kot_id'))
        logger.info(f"KOT CREATE: Database returned max_id: {last_kot['max_id']}")
        
        new_kot_id = (last_kot['max_id'] or 0) + 1
        logger.info(f"KOT CREATE: New KOT ID will be: {new_kot_id}")
        # ---

        # Loop through items and create a Kot entry for each one
        for item_data in items:
            try:
                menu_item = MenuItem.objects.get(id=item_data.get('id'))
            except MenuItem.DoesNotExist:
                menu_item = None

            Kot.objects.create(
                kot_id=new_kot_id,  # Use the new numeric ID
                table=table,
                table_name=table_name,
                menu_item=menu_item,
                item_name=item_data.get('name'),
                quantity=item_data.get('qty'),
                price=Decimal(item_data.get('price'))
            )
        
        logger.info(f"KOT CREATE: Successfully created all items for KOT ID: {new_kot_id}")
        return JsonResponse({'success': True, 'kot_id': new_kot_id})

    except Exception as e:
        # THIS IS THE CRITICAL PART
        # It will log the full error traceback to your runserver console
        logger.error(f"KOT CREATE: CRITICAL ERROR in create_kot_view: {str(e)}", exc_info=True)
        
        # Return the error to the frontend so the alert box shows something
        return JsonResponse({'success': False, 'error': f"Internal Server Error: {str(e)}"}, status=500)


def print_kot_view(request, kot_id):
    try:
        # Find all KOT items matching the kot_id
        items = Kot.objects.filter(kot_id=kot_id).order_by('created_at')
        
        if not items.exists():
            return HttpResponse("KOT not found.", status=404)
        
        # Get common info from the first item
        first_item = items.first()
        
        # The kot.html template expects a 'bill' object for table_name and created_at
        # We will create a simple dictionary to mimic that structure
        context_bill = {
            'table_name': first_item.table_name,
            'created_at': first_item.created_at
        }
        
        context = {
            'bill': context_bill, # Pass the mock 'bill' object
            'items': items,      # Pass the queryset of Kot items
            'kot_id': kot_id     # Pass the kot_id itself
        }
        html_string = render_to_string('kot.html', context)

        pdf_file = HTML(string=html_string, base_url=None).write_pdf()

        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="bill_{kot_id}.pdf"'
        return response
        
        # Render the kot.html template
        # return render(request, 'kot.html', context)
    
    except Exception as e:
        return HttpResponse(f"Error generating KOT: {e}", status=500)
    





# 1. Add these imports at the top
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum # Ensure Sum is imported

# ... (other code)

@login_required(login_url='login')
def report_view(request):
    """
    Fetches all bills and calculates Total, Monthly, Weekly, Cash, and Online sales.
    """
    # Fetch all bills
    recent_bills = Bill.objects.order_by('-created_at').all()
    
    # --- 1. Global Totals ---
    total_sales = recent_bills.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_cash = recent_bills.filter(payment_method__icontains='Cash').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_online = recent_bills.filter(payment_method__icontains='online').aggregate(Sum('total_amount'))['total_amount__sum'] or 0

    # --- 2. Date Calculations ---
    now = timezone.now()

    # Calculate Start of Month
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Calculate Start of Week (Monday)
    # now.weekday() returns 0 for Mon, 1 for Tue... 6 for Sun
    start_of_week = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)

    # --- 3. Filtered Totals ---
    # Total Monthly Sale (Bills created on or after start of this month)
    total_monthly_sales = recent_bills.filter(created_at__gte=start_of_month).aggregate(Sum('total_amount'))['total_amount__sum'] or 0

    # Total Weekly Sale (Bills created on or after this Monday)
    total_weekly_sales = recent_bills.filter(created_at__gte=start_of_week).aggregate(Sum('total_amount'))['total_amount__sum'] or 0

    context = {
        'recent_bills': recent_bills,
        'total_sales': total_sales,
        'total_cash': total_cash,
        'total_online': total_online,
        'total_monthly_sales': total_monthly_sales, # Pass to template
        'total_weekly_sales': total_weekly_sales,   # Pass to template
    }
    return render(request, 'report.html', context)
