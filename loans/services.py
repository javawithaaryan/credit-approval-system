"""
Service layer for loan business logic.

Contains credit score calculation, EMI computation, and
loan eligibility checking — separated from views for clean architecture.
"""
from datetime import date

from customers.models import Customer
from loans.models import Loan


def calculate_emi(loan_amount: float, interest_rate: float, tenure: int) -> float:
    """
    Calculate EMI using the compound interest / reducing balance formula.

    Formula:
        monthly_rate = interest_rate / (12 * 100)
        EMI = P * r * (1+r)^n / ((1+r)^n - 1)

    Args:
        loan_amount: Principal loan amount.
        interest_rate: Annual interest rate in percentage.
        tenure: Loan tenure in months.

    Returns:
        Monthly EMI amount (float).
    """
    if interest_rate == 0:
        return loan_amount / tenure if tenure > 0 else 0.0

    monthly_rate = interest_rate / (12 * 100)
    power = (1 + monthly_rate) ** tenure
    emi = loan_amount * monthly_rate * power / (power - 1)
    return round(emi, 2)


def calculate_credit_score(customer_id: int) -> int:
    """
    Calculate a credit score (out of 100) for a given customer.

    Components:
        1. Past loans paid on time (30 pts)
        2. Number of loans taken (25 pts)
        3. Loan activity in current year (20 pts)
        4. Loan approved volume vs approved_limit (25 pts)

    Override: If sum of current active loan amounts > approved_limit,
    credit_score is forced to 0.

    Args:
        customer_id: The primary key of the customer.

    Returns:
        Integer credit score between 0 and 100.
    """
    customer = Customer.objects.get(customer_id=customer_id)
    all_loans = Loan.objects.filter(customer_id=customer_id)

    # --- OVERRIDE CHECK: active loans vs approved limit ---
    active_loans = Loan.objects.filter(
        customer_id=customer_id,
        end_date__gte=date.today(),
    )
    active_loan_total = sum(loan.loan_amount for loan in active_loans)
    if active_loan_total > customer.approved_limit:
        return 0

    # If no loans at all, give max on applicable components
    if not all_loans.exists():
        # score_1 = 0 (no data), score_2 = 25, score_3 = 20, score_4 = 25
        return 70

    # Component 1 — Past loans paid on time (30 points)
    ratios = []
    for loan in all_loans:
        if loan.tenure > 0:
            ratios.append(loan.emis_paid_on_time / loan.tenure)
    avg_ratio = sum(ratios) / len(ratios) if ratios else 0
    score_1 = avg_ratio * 30

    # Component 2 — Number of loans taken (25 points)
    num_loans = all_loans.count()
    if num_loans == 0:
        score_2 = 25
    elif num_loans <= 2:
        score_2 = 20
    elif num_loans <= 5:
        score_2 = 15
    elif num_loans <= 10:
        score_2 = 8
    else:
        score_2 = 0

    # Component 3 — Loan activity in current year (20 points)
    current_year = date.today().year
    current_year_loans = all_loans.filter(start_date__year=current_year).count()
    if current_year_loans == 0:
        score_3 = 20
    elif current_year_loans <= 2:
        score_3 = 15
    elif current_year_loans <= 4:
        score_3 = 8
    else:
        score_3 = 0

    # Component 4 — Loan approved volume (25 points)
    total_loan_volume = sum(loan.loan_amount for loan in all_loans)
    if total_loan_volume <= customer.approved_limit * 0.3:
        score_4 = 25
    elif total_loan_volume <= customer.approved_limit * 0.5:
        score_4 = 20
    elif total_loan_volume <= customer.approved_limit * 0.7:
        score_4 = 15
    elif total_loan_volume <= customer.approved_limit:
        score_4 = 8
    else:
        score_4 = 0

    credit_score = int(score_1 + score_2 + score_3 + score_4)
    return credit_score


def check_loan_eligibility(
    customer_id: int,
    loan_amount: float,
    interest_rate: float,
    tenure: int,
) -> dict:
    """
    Determine whether a customer is eligible for a new loan.

    Runs credit score calculation, applies approval rules based on
    score thresholds, and checks that total EMIs don't exceed 50%
    of the customer's monthly salary.

    Args:
        customer_id: The primary key of the customer.
        loan_amount: Requested loan amount.
        interest_rate: Requested annual interest rate (%).
        tenure: Requested tenure in months.

    Returns:
        dict with keys: approval, interest_rate, corrected_interest_rate,
        tenure, monthly_installment, message.
    """
    customer = Customer.objects.get(customer_id=customer_id)
    credit_score = calculate_credit_score(customer_id)

    corrected_interest_rate = interest_rate
    approved = False
    message = ''

    # --- Rule 1: Credit-score based approval ---
    if credit_score > 50:
        approved = True
    elif 30 < credit_score <= 50:
        if interest_rate > 12:
            approved = True
        else:
            corrected_interest_rate = 12
            approved = True
    elif 10 < credit_score <= 30:
        if interest_rate > 16:
            approved = True
        else:
            corrected_interest_rate = 16
            approved = True
    else:
        # credit_score <= 10
        approved = False
        if credit_score == 0:
            message = 'Loan rejected: credit score is 0 due to debt exceeding approved limit'
        else:
            message = 'Loan rejected due to low credit score'

    # --- Calculate EMI with the (possibly corrected) rate ---
    monthly_installment = calculate_emi(loan_amount, corrected_interest_rate, tenure)

    # --- Rule 2: EMI check (only if still approved) ---
    if approved:
        active_loans = Loan.objects.filter(
            customer_id=customer_id,
            end_date__gte=date.today(),
        )
        current_emis = sum(loan.monthly_repayment for loan in active_loans)
        if (current_emis + monthly_installment) > 0.5 * customer.monthly_salary:
            approved = False
            message = 'Loan rejected: current EMIs exceed 50% of monthly salary'

    if approved:
        message = 'Loan approved'

    return {
        'customer_id': customer_id,
        'approval': approved,
        'interest_rate': interest_rate,
        'corrected_interest_rate': corrected_interest_rate,
        'tenure': tenure,
        'monthly_installment': monthly_installment,
        'message': message,
        'credit_score': credit_score,
    }
