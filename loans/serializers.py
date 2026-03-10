from rest_framework import serializers


class CheckEligibilitySerializer(serializers.Serializer):
    """Serializer for the check-eligibility request."""

    customer_id = serializers.IntegerField()
    loan_amount = serializers.FloatField()
    interest_rate = serializers.FloatField()
    tenure = serializers.IntegerField()


class CreateLoanSerializer(serializers.Serializer):
    """Serializer for the create-loan request."""

    customer_id = serializers.IntegerField()
    loan_amount = serializers.FloatField()
    interest_rate = serializers.FloatField()
    tenure = serializers.IntegerField()


class LoanDetailSerializer(serializers.Serializer):
    """Serializer for the view-loan response."""

    loan_id = serializers.IntegerField()
    customer = serializers.SerializerMethodField()
    loan_amount = serializers.FloatField()
    interest_rate = serializers.FloatField()
    monthly_installment = serializers.FloatField(source='monthly_repayment')
    tenure = serializers.IntegerField()

    def get_customer(self, obj):
        return {
            'id': obj.customer.customer_id,
            'first_name': obj.customer.first_name,
            'last_name': obj.customer.last_name,
            'phone_number': obj.customer.phone_number,
            'age': obj.customer.age,
        }


class LoanListSerializer(serializers.Serializer):
    """Serializer for the view-loans list response."""

    loan_id = serializers.IntegerField()
    loan_amount = serializers.FloatField()
    interest_rate = serializers.FloatField()
    monthly_installment = serializers.FloatField(source='monthly_repayment')
    repayments_left = serializers.SerializerMethodField()

    def get_repayments_left(self, obj):
        return obj.tenure - obj.emis_paid_on_time
