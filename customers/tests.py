from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from .models import Customer


class RegisterCustomerTests(TestCase):
    """Tests for the POST /api/register endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.url = '/api/register'

    def test_register_customer_success(self):
        """Test successful customer registration with correct approved_limit."""
        payload = {
            'first_name': 'John',
            'last_name': 'Doe',
            'age': 30,
            'monthly_income': 50000,
            'phone_number': 9876543210,
        }
        response = self.client.post(self.url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()

        # approved_limit = round(36 * 50000 / 100000) * 100000
        # = round(18.0) * 100000 = 18 * 100000 = 1800000
        self.assertEqual(data['approved_limit'], 1800000)
        self.assertEqual(data['name'], 'John Doe')
        self.assertEqual(data['monthly_income'], 50000)
        self.assertTrue(Customer.objects.filter(customer_id=data['customer_id']).exists())

    def test_register_customer_missing_fields(self):
        """Test registration fails with missing fields."""
        payload = {
            'first_name': 'John',
            # missing last_name, age, monthly_income, phone_number
        }
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
