from django.db import models
from customers.models import Customer


class Loan(models.Model):
    """Model representing a loan in the credit approval system."""

    loan_id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='loans',
    )
    loan_amount = models.FloatField()
    tenure = models.IntegerField(help_text='Tenure in months')
    interest_rate = models.FloatField(help_text='Annual interest rate in %')
    monthly_repayment = models.FloatField(help_text='EMI amount')
    emis_paid_on_time = models.IntegerField(default=0)
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        db_table = 'loans'

    def __str__(self):
        return f"Loan {self.loan_id} - Customer {self.customer_id}"
