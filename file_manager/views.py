from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Customer, RentalOrder
from .forms import CreateUserForm, CustomerForm, RentalOrderForm
from woocommerce import API
from datetime import datetime, timedelta
from openpyxl import Workbook, load_workbook
from decouple import config
import os
import json


wcapi = API(
    url=config('WCAPI_URL'),
    consumer_key=config('WCAPI_CONSUMER_KEY'),
    consumer_secret=config('WCAPI_CONSUMER_SECRET'),
    version="wc/v3"
)

color_theme = '#065821'

# COLLECT ORDER DATA
data = wcapi.get('orders').json()

customer_list = []
order_list = []


def save_customer(last_customer):
    for customer in reversed(Customer.objects.all()[:5]):
        if last_customer == customer:
            break

    customer_list.append(last_customer)
    last_customer.save()


def update_order_db():
    for i in data:
        current_order = i
        f_name = current_order['billing']['first_name']
        l_name = current_order['billing']['last_name']
        phone = current_order['billing']['phone']
        email = current_order['billing']['email']
        street = current_order['billing']['address_1']
        apt_suite_other = current_order['billing']['address_2']
        city = current_order['billing']['city']
        state = current_order['billing']['state']
        zip_code = current_order['billing']['postcode']

        last_customer = Customer(
            first=f_name,
            last=l_name,
            phone=phone,
            email=email,
            street=street,
            apt_suite_other=apt_suite_other,
            city=city,
            state=state,
            zip_code=zip_code
        )

        try:
            last_customer = Customer.objects.get(first=last_customer.first, last=last_customer.last)
        except Customer.DoesNotExist:
            last_customer.save()

        invoice = current_order['id']
        date = datetime.strptime(current_order['date_created'], '%Y-%m-%dT%H:%M:%S').date()
        delivery_street = current_order['shipping']['address_1']
        delivery_apt_suite_other = current_order['shipping']['address_2']
        delivery_city = current_order['shipping']['city']
        delivery_state = current_order['shipping']['state']
        delivery_zip_code = current_order['shipping']['postcode']
        pickup_address = current_order['meta_data'][4]['value']
        total_price = current_order['total']

        delivery_datetime = current_order['meta_data'][0]['value'] + current_order['meta_data'][1]['value']
        try:
            delivery_date = datetime.strptime(current_order['meta_data'][0]['value'], '%Y-%m-%d')
        except ValueError:
            try:
                delivery_date = datetime.strptime(current_order['meta_data'][0]['value'], '%m/%d/%Y')
            except ValueError:
                try:
                    delivery_date = datetime.strptime(current_order['meta_data'][0]['value'], '%B %d, %Y')
                except ValueError:
                    try:
                        delivery_date = datetime.strptime(current_order['meta_data'][0]['value'], '%B %dth %Y')
                    except ValueError:
                        try:
                            delivery_date = datetime.strptime(current_order['meta_data'][0]['value'], '%B %st %Y')
                        except ValueError:
                            try:
                                delivery_date = datetime.strptime(current_order['meta_data'][0]['value'], '%B %dnd %Y')
                            except ValueError:
                                delivery_date = datetime.strptime(current_order['meta_data'][0]['value'], '%B %drd %Y')

        try:
            delivery_datetime = datetime.strptime(delivery_datetime, '%Y-%m-%d%H:%M')
        except ValueError:
            try:
                delivery_datetime = datetime.strptime(delivery_datetime, '%m/%d/%Y%H:%M %p')
            except ValueError:
                try:
                    delivery_datetime = datetime.strptime(delivery_datetime, '%B %dth %Y%H%p')
                except ValueError:
                    try:
                        delivery_datetime = datetime.strptime(delivery_datetime, '%B %d, %Y%H%p')
                    except ValueError:
                        delivery_datetime = None

        delivery_date = delivery_date.date()

        # THIS LOCATES THE RENTAL PERIOD AND CREATES PICKUP DATETIME OBJECT
        try:
            rental_period = int(current_order['line_items'][0]['meta_data'][0]['value'][0])
            if rental_period == 1:
                pickup_date = delivery_date + timedelta(days=7)
                rental_period = '1 Week'
            elif rental_period == 2:
                pickup_date = delivery_date + timedelta(days=14)
                rental_period = '2 Weeks'
            elif rental_period == 3:
                pickup_date = delivery_date + timedelta(days=21)
                rental_period = '3 Weeks'
            elif rental_period == 4:
                pickup_date = delivery_date + timedelta(days=28)
                rental_period = '4 Weeks'
        except IndexError:
            rental_period = '1 Week'
            pickup_date = delivery_date + timedelta(days=7)

        for x in range(len(current_order['line_items'])):
            if current_order['line_items'][x]['product_id'] == 1270:
                lg_boxes = 70
                xl_boxes = 10
                lg_dollies = 4
                xl_dollies = 2
                labels = 80
                zip_ties = 80
                bins = 0
                break
            elif current_order['line_items'][x]['product_id'] == 1515:
                lg_boxes = 50
                xl_boxes = 10
                lg_dollies = 3
                xl_dollies = 1
                labels = 60
                zip_ties = 60
                bins = 0
                break
            elif current_order['line_items'][x]['product_id'] == 1510:
                lg_boxes = 35
                xl_boxes = 5
                lg_dollies = 2
                xl_dollies = 0
                labels = 40
                zip_ties = 40
                bins = 0
            elif current_order['line_items'][x]['product_id'] == 1505:
                lg_boxes = 18
                xl_boxes = 2
                lg_dollies = 1
                xl_dollies = 0
                labels = 20
                zip_ties = 20
                bins = 0
                break
            elif current_order['line_items'][x]['product_id'] == 1545:
                lg_boxes = 1
                xl_boxes = 0
                lg_dollies = 0
                xl_dollies = 0
                labels = 0
                zip_ties = 0
                bins = 0
                break
            elif current_order['line_items'][x]['product_id'] == 1291:
                lg_boxes = 0
                xl_boxes = 0
                lg_dollies = 0
                xl_dollies = 0
                labels = 0
                zip_ties = 0
                bins = current_order['line_items'][x]['quantity']
                break
            else:
                lg_boxes = 0
                xl_boxes = 0
                lg_dollies = 0
                xl_dollies = 0
                labels = 0
                zip_ties = 0
                bins = 0

        last_order = RentalOrder(
            invoice=invoice,
            date=date,
            customer=last_customer,
            lg_boxes=lg_boxes,
            xl_boxes=xl_boxes,
            lg_dollies=lg_dollies,
            xl_dollies=xl_dollies,
            labels=labels,
            zip_ties=zip_ties,
            bins=bins,
            delivery_date=delivery_date,
            delivery_street=delivery_street,
            delivery_apt_suite_other=delivery_apt_suite_other,
            delivery_city=delivery_city,
            delivery_state=delivery_state,
            delivery_zip_code=delivery_zip_code,
            rental_period=rental_period,
            pickup_date=pickup_date,
            total_price=total_price,
            pickup_address=pickup_address,
        )

        try:
            RentalOrder.objects.get(invoice=last_order.invoice)
        except RentalOrder.DoesNotExist:
            last_order.save()


# Create your views here.
@require_POST
def webhook(request):
    print(wcapi.get("webhooks/2").json())
    return HttpResponse('This is the webhook response')


def web_orders(request):
    context = {
        'customer_list': customer_list,
        'order_list': order_list,
        'color_theme': color_theme
    }

    return render(request, 'file_manager/web_orders.html', context)


@login_required(login_url='/login')
def home(request):
    # update_order_db()
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


def export_order_file(request, invoice):
    details = get_object_or_404(RentalOrder, invoice=invoice)

    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = f'attachment; filename="{details.customer.full_name()}{details.invoice}.xlsx"'

    path = os.path.dirname(__file__)
    file = os.path.join(path, 'rental_order.xlsx')
    wb = load_workbook(file)
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
    ws['G34'] = details.total_price
    ws['B21'] = details.lg_boxes
    ws['B22'] = details.xl_boxes
    ws['B23'] = details.lg_dollies
    ws['B24'] = details.xl_dollies
    ws['B25'] = details.labels
    ws['B26'] = details.zip_ties
    ws['B27'] = details.bins

    wb.save(response)
    return response


@login_required(login_url='/login')
def customer_details(request):
    search = request.POST.get('search')
    context = {
        'search': search,
    }

    return render(request, 'file_manager/customer_details.html', context)


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


@login_required(login_url='/login')
def rental_order_form(request):
    form = RentalOrderForm()

    if request.method == 'POST':
        form = RentalOrderForm(request.POST)
        if form.is_valid():
            form.save()

    context = {'form': form}
    return render(request, 'file_manager/rental_order_form.html', context)


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


@login_required(login_url='/login')
def display_orders(request):
    # update_order_db()
    rental_orders = RentalOrder.objects.all().order_by('-invoice')

    context = {
        'rental_orders': rental_orders,
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
