import datetime

from django.utils import timezone
from django.test import TestCase
from django.urls import reverse

from .models import Customer, RentalOrder
# Create your tests here.


class RentalOrderModelTests(TestCase):

    def test_recent_order_with_future_order(self):
        time = timezone.now() + datetime.timedelta(days=30)
        time.date()
        future_o = RentalOrder(date=time)
        self.assertIs(future_o.recent_order(), False)

    def test_recent_order_with_old_order(self):
        time = timezone.now() - datetime.timedelta(days=8)
        time.date()
        future_o = RentalOrder(date=time)
        self.assertIs(future_o.recent_order(), False)

    def test_recent_order_with_recent_order(self):
        time = timezone.now() - datetime.timedelta(days=3)
        time.date()
        future_o = RentalOrder(date=time)
        self.assertIs(future_o.recent_order(), True)

    def test_upcoming_with_upcoming_delivery_date(self):
        date = timezone.now() + datetime.timedelta(days=3)
        date.date()
        future_o = RentalOrder(delivery_date=date)
        self.assertIs(future_o.upcoming(), True)

    def test_upcoming_with_past_delivery_date(self):
        date = timezone.now() - datetime.timedelta(days=3)
        date.date()
        future_o = RentalOrder(delivery_date=date)
        self.assertIs(future_o.upcoming(), False)

    def test_upcoming_with_far_away_delivery_date(self):
        date = timezone.now() - datetime.timedelta(days=15)
        date = date.date()
        future_order = RentalOrder(delivery_date=date)
        self.assertIs(future_order.upcoming(), False)

class CustomerModelTests(TestCase):
    pass
