from rest_framework import serializers
from .models import Customer


class RegisterCustomerSerializer(serializers.Serializer):
    """Serializer for customer registration request."""

    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    age = serializers.IntegerField()
    monthly_income = serializers.IntegerField()
    phone_number = serializers.IntegerField()


class CustomerResponseSerializer(serializers.Serializer):
    """Serializer for customer registration response."""

    customer_id = serializers.IntegerField()
    name = serializers.CharField()
    age = serializers.IntegerField()
    monthly_income = serializers.IntegerField()
    approved_limit = serializers.IntegerField()
    phone_number = serializers.IntegerField()
