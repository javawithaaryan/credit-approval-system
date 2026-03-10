from datetime import date
from dateutil.relativedelta import relativedelta

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from customers.models import Customer
from .models import Loan
from .serializers import (
    CheckEligibilitySerializer,
    CreateLoanSerializer,
    LoanDetailSerializer,
    LoanListSerializer,
)
from .services import check_loan_eligibility, calculate_emi


@api_view(['POST'])
def check_eligibility(request):
    """
    Check if a customer is eligible for a loan.

    Delegates to the service layer for credit score and eligibility logic.
    """
    serializer = CheckEligibilitySerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    try:
        result = check_loan_eligibility(
            customer_id=data['customer_id'],
            loan_amount=data['loan_amount'],
            interest_rate=data['interest_rate'],
            tenure=data['tenure'],
        )
    except Customer.DoesNotExist:
        return Response(
            {'message': 'Customer not found'},
            status=status.HTTP_404_NOT_FOUND,
        )

    return Response({
        'customer_id': result['customer_id'],
        'approval': result['approval'],
        'interest_rate': result['interest_rate'],
        'corrected_interest_rate': result['corrected_interest_rate'],
        'tenure': result['tenure'],
        'monthly_installment': result['monthly_installment'],
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
def create_loan(request):
    """
    Create a new loan after checking eligibility.

    If approved, creates the Loan record in the DB.
    If not approved, returns loan_id as null.
    """
    serializer = CreateLoanSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    try:
        result = check_loan_eligibility(
            customer_id=data['customer_id'],
            loan_amount=data['loan_amount'],
            interest_rate=data['interest_rate'],
            tenure=data['tenure'],
        )
    except Customer.DoesNotExist:
        return Response(
            {'message': 'Customer not found'},
            status=status.HTTP_404_NOT_FOUND,
        )

    if result['approval']:
        today = date.today()
        end_date = today + relativedelta(months=data['tenure'])
        loan = Loan.objects.create(
            customer_id=data['customer_id'],
            loan_amount=data['loan_amount'],
            tenure=data['tenure'],
            interest_rate=result['corrected_interest_rate'],
            monthly_repayment=result['monthly_installment'],
            emis_paid_on_time=0,
            start_date=today,
            end_date=end_date,
        )
        return Response({
            'loan_id': loan.loan_id,
            'customer_id': data['customer_id'],
            'loan_approved': True,
            'message': result['message'],
            'monthly_installment': result['monthly_installment'],
        }, status=status.HTTP_201_CREATED)
    else:
        return Response({
            'loan_id': None,
            'customer_id': data['customer_id'],
            'loan_approved': False,
            'message': result['message'],
            'monthly_installment': result['monthly_installment'],
        }, status=status.HTTP_200_OK)


@api_view(['GET'])
def view_loan(request, loan_id):
    """View details of a specific loan."""
    try:
        loan = Loan.objects.select_related('customer').get(loan_id=loan_id)
    except Loan.DoesNotExist:
        return Response(
            {'message': 'Loan not found'},
            status=status.HTTP_404_NOT_FOUND,
        )

    serializer = LoanDetailSerializer(loan)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
def view_loans(request, customer_id):
    """View all loans for a specific customer."""
    if not Customer.objects.filter(customer_id=customer_id).exists():
        return Response(
            {'message': 'Customer not found'},
            status=status.HTTP_404_NOT_FOUND,
        )

    loans = Loan.objects.filter(customer_id=customer_id)
    serializer = LoanListSerializer(loans, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)
