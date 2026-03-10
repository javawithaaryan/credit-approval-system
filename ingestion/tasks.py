"""
Celery tasks for background data ingestion.

Reads customer_data.xlsx and loan_data.xlsx from the /app/data directory
and bulk-creates Customer and Loan objects if the tables are empty.
"""
import os
import logging
from datetime import datetime

from celery import shared_task
from django.conf import settings

logger = logging.getLogger(__name__)


@shared_task(name='ingestion.tasks.ingest_data')
def ingest_data():
    """
    Ingest customer and loan data from Excel files into the database.

    Only runs if the Customer and Loan tables are empty to prevent
    duplicate ingestion. Uses bulk_create for efficiency.
    """
    from customers.models import Customer
    from loans.models import Loan
    import openpyxl

    data_dir = getattr(settings, 'DATA_DIR', os.path.join(settings.BASE_DIR, 'data'))

    # --- Ingest Customers ---
    if not Customer.objects.exists():
        customer_file = os.path.join(data_dir, 'customer_data.xlsx')
        if os.path.exists(customer_file):
            logger.info('Ingesting customer data from %s', customer_file)
            wb = openpyxl.load_workbook(customer_file, read_only=True)
            ws = wb.active
            rows = list(ws.iter_rows(min_row=2, values_only=True))
            customers = []
            for row in rows:
                if row[0] is None:
                    continue
                customers.append(Customer(
                    customer_id=int(row[0]),
                    first_name=str(row[1]).strip(),
                    last_name=str(row[2]).strip(),
                    age=int(row[3]),
                    phone_number=int(row[4]),
                    monthly_salary=int(row[5]),
                    approved_limit=int(row[6]),
                    current_debt=0.0,
                ))
            Customer.objects.bulk_create(customers, batch_size=1000)
            wb.close()
            logger.info('Successfully ingested %d customers', len(customers))
        else:
            logger.warning('Customer data file not found: %s', customer_file)
    else:
        logger.info('Customer table already has data, skipping ingestion.')

    # --- Ingest Loans ---
    if not Loan.objects.exists():
        loan_file = os.path.join(data_dir, 'loan_data.xlsx')
        if os.path.exists(loan_file):
            logger.info('Ingesting loan data from %s', loan_file)
            wb = openpyxl.load_workbook(loan_file, read_only=True)
            ws = wb.active
            rows = list(ws.iter_rows(min_row=2, values_only=True))
            loans = []
            for row in rows:
                if row[0] is None:
                    continue
                # Parse dates - handle both string and datetime objects
                emis_paid_on_time = int(row[6])
                start_date = row[7]
                end_date = row[8]
                if isinstance(start_date, str):
                    start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                elif isinstance(start_date, datetime):
                    start_date = start_date.date()

                if isinstance(end_date, str):
                    end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                elif isinstance(end_date, datetime):
                    end_date = end_date.date()

                loans.append(Loan(
                    customer_id=int(row[0]),
                    loan_id=int(row[1]),
                    loan_amount=float(row[2]),
                    tenure=int(row[3]),
                    interest_rate=float(row[4]),
                    monthly_repayment=float(row[5]),
                    emis_paid_on_time=emis_paid_on_time,
                    start_date=start_date,
                    end_date=end_date,
                ))
            Loan.objects.bulk_create(loans, batch_size=1000)
            wb.close()
            logger.info('Successfully ingested %d loans', len(loans))
        else:
            logger.warning('Loan data file not found: %s', loan_file)
    else:
        logger.info('Loan table already has data, skipping ingestion.')

    return 'Data ingestion complete'
