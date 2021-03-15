from __future__ import print_function

import os
import os.path

from decouple import config
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from openpyxl import load_workbook
from woocommerce import API

from webhooks import views as views
from .forms import CreateUserForm, CustomerForm, RentalOrderForm
from .models import Customer, RentalOrder

# This will establish the WooCommerce API to make calls
wcapi = API(
    url=config('WCAPI_URL'),
    consumer_key=config('WCAPI_CONSUMER_KEY'),
    consumer_secret=config('WCAPI_CONSUMER_SECRET'),
    version="wc/v3"
)

color_theme = '#065821'


# Function uses google calendar event json objects for delivery and pickup events
def post_events(delivery, pickup):

    SCOPES = ['https://www.googleapis.com/auth/calendar']

    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open('token.json', 'w') as token:
        token.write(creds.to_json())

    service = build('calendar', 'v3', credentials=creds)


# Call the Calendar API
    delivery = service.events().insert(calendarId='primary',
                                       sendNotifications=False,
                                       body=delivery).execute()

    pickup = service.events().insert(calendarId='primary',
                                     sendNotifications=False,
                                     body=pickup).execute()

    return [delivery.get('htmlLink'), pickup.get('htmlLink')]

# VIEW PAGES ARE BELOW


@login_required(login_url='/login')
def home(request):

    search = request.POST.get('search')

    # THIS CREATES LIST OBJECT OF RECENT & UPCOMING ORDERS ORDERED BY DATE
    last_orders = RentalOrder.objects.all()
    recent_orders = []
    upcoming_orders = []
    for order in last_orders:
        if order.recent_order():
            recent_orders.append(order)

    for order in last_orders:
        if order.upcoming():
            upcoming_orders.append(order)

    # CREATE A DICT OBJ CONTEXT FOR NEW LIST
    context = {
        'recent_orders': recent_orders,
        'upcoming_orders': upcoming_orders,
        'search': search,
    }
    return render(request, 'file_manager/home.html', context)


@login_required(login_url='/login')
def new_search(request):
    search = request.POST.get('search').capitalize()
    try:
        c_results = Customer.objects.get(first=search)
    except Customer.DoesNotExist:
        results = None
    else:
        results = RentalOrder.objects.filter(customer=c_results)

    context = {
        'search': search,
        'orders': results
    }

    return render(request, 'file_manager/new_search.html', context)


@login_required(login_url='/login')
def order_details(request, invoice):
    details = get_object_or_404(RentalOrder, invoice=invoice)

    context = {
        'details': details,
    }
    return render(request, 'file_manager/order_details.html', context)


# CREATE DELIVERY AND PICKUP EVENTS TO POST TO GOOGLE CALENDAR

@login_required(login_url='/login')
def create_events(request, invoice):

    # RETRIEVE ORDER & CUSTOMER INFO FROM DJANGO DB USING
    # INVOICE # FOR THE ORDER & CUSTOMER FIRST NAME
    order = get_object_or_404(RentalOrder, invoice=invoice)
    customer = get_object_or_404(Customer, first=order.customer.first)

    # FUNCTIONS LOCATED IN WEBHOOKS.VIEWS TO CREATE EVENTS FOR DELIVERY & PICKUP
    delivery = views.create_delivery_event(order, customer)
    pickup = views.create_pickup_event(order, customer)

    print(delivery)
    print("")
    print(pickup)

    created_event_links = post_events(delivery, pickup)
    print(created_event_links)

    context = {
        'delivery_link': created_event_links[0],
        'pickup_link': created_event_links[1],
        'order': order
    }

    return render(request, 'file_manager/create_events.html', context)


# THIS ALLOWS FOR THE USER TO DOWNLOAD AN EXCEL FILE CONTAINING RENTAL ORDER & CUSTOMER INFORMATION
def export_order_file(request, invoice):

    # RETRIEVE ORDER DETAILS FROM DB
    details = get_object_or_404(RentalOrder, invoice=invoice)

    # NOT EXACTLY SURE HOW THIS CODE WORKS
    response = HttpResponse(content_type='application/ms-excel')

    # CREATES NEW FILENAME FOR WORKBOOK TO BE SAVED AS
    response['Content-Disposition'] = f'attachment; filename="{details.customer.full_name()}{details.invoice}.xlsx"'

    path = os.path.dirname(__file__)
    file = os.path.join(path, 'rental_order.xlsx')

    # LOAD TEMPLATE WORKBOOK FROM FILE
    wb = load_workbook(file)

    # LOAD WORKSHEET FROM WORKBOOK.ACTIVE AND ASSIGN ALL NECESSARY INFO INTO WS CELLS
    ws = wb.active
    ws['G3'] = details.date
    ws['G4'] = details.invoice
    ws['C7'] = details.customer.full_name()
    ws['C8'] = details.customer.street
    ws['C9'] = f'{details.customer.city}, {details.customer.state} {details.customer.zip_code}'
    ws['C10'] = details.customer.phone
    ws['C11'] = details.customer.email
    ws['F7'] = details.delivery_street
    ws['F8'] = f'{details.delivery_city}, {details.delivery_state} {details.delivery_zip_code}'
    ws['F11'] = details.pickup_address
    ws['F16'] = details.delivery_date
    ws['G16'] = details.pickup_date
    ws['B18'] = details.rental_period
    ws['G18'] = details.was_delivered()
    # ws['G34'] = details.total_price
    ws['B21'] = details.lg_boxes
    ws['B22'] = details.xl_boxes
    ws['B23'] = details.lg_dollies
    ws['B24'] = details.xl_dollies
    ws['B25'] = details.labels
    ws['B26'] = details.zip_ties
    ws['B27'] = details.bins

    # SAVE WORKBOOK INTO NEW FILENAME SAVED INSIDE RESPONSE VARIABLE
    wb.save(response)
    return response


@login_required(login_url='/login')
def customer_details(request):
    search = request.POST.get('search')
    context = {
        'search': search,
    }

    return render(request, 'file_manager/customer_details.html', context)


# HANDLES USER INPUT FOR CUSTOMER FORM TO SAVE NEW CUSTOMER INTO DB
@login_required(login_url='/login')
def customer_form(request):
    form = CustomerForm()

    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            form.save()

    context = {'form': form,
               }
    return render(request, 'file_manager/customer_form.html', context)


# HANDLES USER INPUT FOR RENTAL ORDER FORM TO SAVE NEW ORDER INTO DB
@login_required(login_url='/login')
def rental_order_form(request):
    form = RentalOrderForm()

    if request.method == 'POST':
        form = RentalOrderForm(request.POST)
        if form.is_valid():
            form.save()

    context = {'form': form}
    return render(request, 'file_manager/rental_order_form.html', context)


# HANDLES USER INPUT FOR UPDATING EXISTING ORDERS AND SAVES NEW INFO INTO DB
@login_required(login_url='/login')
def update_order_form(request, pk):

    order = RentalOrder.objects.get(id=pk)
    form = RentalOrderForm(instance=order)

    if request.method == 'POST':
        form = RentalOrderForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            return redirect('/orders')
    context = {'form': form}
    return render(request, 'file_manager/update_order.html', context)


@login_required(login_url='/login')
def delete_order(request, pk):
    order = RentalOrder.objects.get(id=pk)

    if request.method == 'POST':
        order.delete()
        return redirect('/orders')

    context = {'order': order}
    return render(request, 'file_manager/delete.html', context)


# THIS VIEW LISTS MOST RECENT RENTAL ORDERS
@login_required(login_url='/login')
def display_orders(request):
    # data = wcapi.get('orders?page=4').json()

    # for order in range(len(data)):
    #     views.update_order_db(order)

    # RETRIEVE RENTAL ORDER LIST FROM DJANGO DB ORDERED BY MOST RECENT INVOICE
    rental_orders = RentalOrder.objects.all().order_by('-invoice')

    # PAGINATOR CLASS WILL LIST ORDERS 10 PER PAGE
    p = Paginator(rental_orders, 10)
    page_num = request.GET.get('page')
    page = p.get_page(page_num)

    context = {
        'page_obj': p,
        'page': page
    }
    return render(request, 'file_manager/all_orders.html', context)


@login_required(login_url='/login')
def storage(request):
    return render(request, 'file_manager/storage.html')


def login_page(request):
    if request.user.is_authenticated:
        return redirect('file_manager-home')
    else:
        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')

            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('file_manager-home')
            else:
                messages.info(request, 'Username OR Password is incorrect')

        return render(request, 'file_manager/login.html')


@login_required(login_url='/login')
def register_page(request):
    if request.user.is_authenticated:
        return redirect('file_manager-home')
    else:
        form = CreateUserForm()

        if request.method == 'POST':
            form = CreateUserForm(request.POST)
            if form.is_valid():
                form.save()
                user = form.cleaned_data.get('username')
                messages.success(request, 'Account was created for ' + user)

                return redirect('/login')

        context = {
            'form': form,
        }
        return render(request, 'file_manager/register.html', context)


def logout_user(request):
    logout(request)

    return redirect('/login')

