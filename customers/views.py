from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Customer
from .serializers import RegisterCustomerSerializer, CustomerResponseSerializer


@api_view(['POST'])
def register_customer(request):
    """
    Register a new customer.

    Calculates approved_limit as round(36 * monthly_income / 100000) * 100000
    and saves the customer to the database.
    """
    serializer = RegisterCustomerSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    monthly_income = data['monthly_income']

    # Calculate approved_limit rounded to nearest lakh
    approved_limit = round(36 * monthly_income / 100000) * 100000

    customer = Customer.objects.create(
        first_name=data['first_name'],
        last_name=data['last_name'],
        age=data['age'],
        phone_number=data['phone_number'],
        monthly_salary=monthly_income,
        approved_limit=approved_limit,
        current_debt=0.0,
    )

    response_data = {
        'customer_id': customer.customer_id,
        'name': f"{customer.first_name} {customer.last_name}",
        'age': customer.age,
        'monthly_income': customer.monthly_salary,
        'approved_limit': customer.approved_limit,
        'phone_number': customer.phone_number,
    }

    return Response(response_data, status=status.HTTP_201_CREATED)
