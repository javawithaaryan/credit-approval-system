from django.db import models


class Customer(models.Model):
    """Model representing a customer in the credit approval system."""

    customer_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    age = models.IntegerField()
    phone_number = models.BigIntegerField()
    monthly_salary = models.IntegerField()
    approved_limit = models.IntegerField()
    current_debt = models.FloatField(default=0)

    class Meta:
        db_table = 'customers'

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
