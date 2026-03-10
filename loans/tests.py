from datetime import date, timedelta

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from customers.models import Customer
from loans.models import Loan


class CheckEligibilityTests(TestCase):
    """Tests for the POST /api/check-eligibility endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.url = '/api/check-eligibility'
        self.customer = Customer.objects.create(
            first_name='Alice',
            last_name='Smith',
            age=28,
            phone_number=9876543210,
            monthly_salary=80000,
            approved_limit=2900000,
            current_debt=0,
        )

    def test_check_eligibility_high_credit_score(self):
        """Customer with no loans should have a high credit score → approved."""
        payload = {
            'customer_id': self.customer.customer_id,
            'loan_amount': 500000,
            'interest_rate': 10,
            'tenure': 24,
        }
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(data['approval'])

    def test_check_eligibility_exceeds_emi_limit(self):
        """EMI for existing + new loan exceeds 50% salary → rejected."""
        # Create a large existing active loan
        Loan.objects.create(
            customer=self.customer,
            loan_amount=2000000,
            tenure=60,
            interest_rate=10,
            monthly_repayment=42000,  # > 50% of 80000
            emis_paid_on_time=10,
            start_date=date.today() - timedelta(days=30),
            end_date=date.today() + timedelta(days=1800),
        )
        payload = {
            'customer_id': self.customer.customer_id,
            'loan_amount': 100000,
            'interest_rate': 10,
            'tenure': 12,
        }
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertFalse(data['approval'])


class CreateLoanTests(TestCase):
    """Tests for the POST /api/create-loan endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.url = '/api/create-loan'
        self.customer = Customer.objects.create(
            first_name='Bob',
            last_name='Jones',
            age=35,
            phone_number=9123456789,
            monthly_salary=100000,
            approved_limit=3600000,
            current_debt=0,
        )

    def test_create_loan_approved(self):
        """Eligible customer gets a loan approved and created in DB."""
        payload = {
            'customer_id': self.customer.customer_id,
            'loan_amount': 200000,
            'interest_rate': 10,
            'tenure': 24,
        }
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertTrue(data['loan_approved'])
        self.assertIsNotNone(data['loan_id'])
        self.assertTrue(Loan.objects.filter(loan_id=data['loan_id']).exists())

    def test_create_loan_rejected(self):
        """Customer with credit_score = 0 gets rejection, loan_id is null."""
        # Make active debt exceed approved_limit so credit_score = 0
        Loan.objects.create(
            customer=self.customer,
            loan_amount=4000000,
            tenure=60,
            interest_rate=10,
            monthly_repayment=10000,
            emis_paid_on_time=5,
            start_date=date.today() - timedelta(days=30),
            end_date=date.today() + timedelta(days=1800),
        )
        payload = {
            'customer_id': self.customer.customer_id,
            'loan_amount': 100000,
            'interest_rate': 10,
            'tenure': 12,
        }
        response = self.client.post(self.url, payload, format='json')
        data = response.json()
        self.assertFalse(data['loan_approved'])
        self.assertIsNone(data['loan_id'])


class ViewLoanTests(TestCase):
    """Tests for the GET /api/view-loan/<id> endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.customer = Customer.objects.create(
            first_name='Carol',
            last_name='Davis',
            age=40,
            phone_number=9988776655,
            monthly_salary=60000,
            approved_limit=2200000,
            current_debt=0,
        )
        self.loan = Loan.objects.create(
            customer=self.customer,
            loan_amount=300000,
            tenure=36,
            interest_rate=12,
            monthly_repayment=9967.01,
            emis_paid_on_time=10,
            start_date=date.today() - timedelta(days=300),
            end_date=date.today() + timedelta(days=800),
        )

    def test_view_loan_success(self):
        """Successfully view an existing loan with customer details."""
        url = f'/api/view-loan/{self.loan.loan_id}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['loan_id'], self.loan.loan_id)
        self.assertEqual(data['customer']['id'], self.customer.customer_id)
        self.assertEqual(data['customer']['first_name'], 'Carol')

    def test_view_loan_not_found(self):
        """Return 404 for non-existent loan."""
        response = self.client.get('/api/view-loan/99999')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ViewLoansTests(TestCase):
    """Tests for the GET /api/view-loans/<customer_id> endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.customer = Customer.objects.create(
            first_name='Dave',
            last_name='Evans',
            age=32,
            phone_number=9912345678,
            monthly_salary=70000,
            approved_limit=2500000,
            current_debt=0,
        )

    def test_view_loans_by_customer(self):
        """Get list of loans for a customer with repayments_left calculated."""
        Loan.objects.create(
            customer=self.customer,
            loan_amount=100000, tenure=12, interest_rate=10,
            monthly_repayment=8792.0, emis_paid_on_time=4,
            start_date=date.today() - timedelta(days=120),
            end_date=date.today() + timedelta(days=240),
        )
        Loan.objects.create(
            customer=self.customer,
            loan_amount=200000, tenure=24, interest_rate=12,
            monthly_repayment=9415.0, emis_paid_on_time=6,
            start_date=date.today() - timedelta(days=180),
            end_date=date.today() + timedelta(days=540),
        )
        url = f'/api/view-loans/{self.customer.customer_id}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data), 2)
        # First loan: repayments_left = 12 - 4 = 8
        self.assertEqual(data[0]['repayments_left'], 8)
