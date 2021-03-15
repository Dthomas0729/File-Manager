from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from file_manager.models import Customer, RentalOrder
from woocommerce import API
from datetime import datetime, timedelta
from decouple import config
import os
import pickle
from googleapiclient.discovery import build
from google.oauth2 import service_account

wcapi = API(
    url=config('WCAPI_URL'),
    consumer_key=config('WCAPI_CONSUMER_KEY'),
    consumer_secret=config('WCAPI_CONSUMER_SECRET'),
    version="wc/v3")

# COLLECT ORDER DATA
data = wcapi.get('orders').json()


def update_order_db():
    current_order = data[0]
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
        return [last_order, last_customer]

    except RentalOrder.DoesNotExist:
        last_order.save()
        return [last_order, last_customer]


def post_events(delivery, pickup):

    SCOPES = ['https://www.googleapis.com/auth/calendar']

    service_account_file = 'taggabox-web-app-d02e1e73d5cf.json'

    credentials = service_account.Credentials.from_service_account_file(
        service_account_file, scopes=SCOPES)
    credentials = credentials.with_subject('taggabox-order-update@flowing-blade-284003.iam.gserviceaccount.com')

    service = build('calendar', 'v3', credentials=credentials)

# Call the Calendar API
    service.events().insert(calendarId='primary', body=delivery).execute()
    service.events().insert(calendarId='primary', body=pickup).execute()


def create_delivery_event(last_order, customer):

    start_time = last_order.delivery_date
    start_time = start_time.strftime('%Y-%m-%dT%H:%M:%S-04:00')

    end_time = last_order.delivery_date + timedelta(hours=1)
    end_time = end_time.strftime('%Y-%m-%dT%H:%M:%S-04:00')

    delivery_event = {
        'summary': f'{customer.first} {customer.last} Box Delivery',
        'location': f'{last_order.delivery_street}, {last_order.delivery_city}, {last_order.delivery_state} {last_order.delivery_zip_code}',
        'description': f'''{customer.first} {customer.last}
phone: {customer.phone}
address: {last_order.delivery_street}, {last_order.delivery_city}, {last_order.delivery_state} {last_order.delivery_zip_code}
email: {customer.email}
{last_order.lg_boxes} Lg Boxes
{last_order.xl_boxes} Xl Boxes
{last_order.lg_dollies} Dollies
{last_order.xl_dollies} Xl Dollies
{last_order.labels} Labels & Zip Ties
{last_order.bins} Bins''',

        'start': {
            'dateTime': f'{start_time}',
            'timeZone': 'America/New_York',
        },
        'end': {
            'dateTime': f'{end_time}',
            'timeZone': 'America/New_York',
        },
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'email', 'minutes': 24 * 60},
                {'method': 'popup', 'minutes': 10},
            ],
        },
    }
    return delivery_event


def create_pickup_event(last_order, customer):
    start_time = last_order.pickup_date
    start_time = start_time.strftime('%Y-%m-%dT%H:%M:%S-04:00')

    end_time = last_order.pickup_date + timedelta(hours=1)
    end_time = end_time.strftime('%Y-%m-%dT%H:%M:%S-04:00')

    pickup_event = {
        'summary': f'{customer.first} {customer.last} Box Pick Up',
        'location': f'{last_order.pickup_address}',
        'description': f'''{customer.first} {customer.last}
phone: {customer.phone}
Address {last_order.pickup_address}
email: {customer.email}
{last_order.lg_boxes} Lg Boxes                                                                      
{last_order.xl_boxes} Xl Boxes
{last_order.lg_dollies} Dollies
{last_order.xl_dollies} Xl Dollies
{last_order.labels} Labels & Zip Ties
{last_order.bins} Bins''',

        'start': {
            'dateTime': f'{start_time}',
            'timeZone': 'America/New_York',
        },
        'end': {
            'dateTime': f'{end_time}',
            'timeZone': 'America/New_York',
        },
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'email', 'minutes': 24 * 60},
                {'method': 'popup', 'minutes': 10},
            ],
        },
    }
    return pickup_event


@csrf_exempt
@require_POST
def update_order(request):
    order = update_order_db()[0]
    customer = update_order_db()[1]

    delivery = create_delivery_event(order, customer)
    pickup = create_pickup_event(order, customer)

    # print(f'{delivery["summary"]} Event Created')
    print(delivery)


    # post_events(delivery, pickup)

    return HttpResponse('Hello, world. This is the webhook response.')
