# Credit Approval System

A production-ready **Credit Approval System** built with Django REST Framework, PostgreSQL, Celery, and Redis — fully containerised with Docker.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.11 |
| Framework | Django 4.2 + DRF 3.14 |
| Database | PostgreSQL 15 |
| Task Queue | Celery 5.3 + Redis 7 |
| Container | Docker + Docker Compose |

## Quick Start

```bash
# Clone the repo
git clone https://github.com/javawithaaryan/credit-approval-system.git
cd credit-approval-system

# Start all services
docker-compose up --build
```

The API will be available at `http://localhost:8000/api/`.

On first startup, the Celery worker automatically ingests **303 customers** and **782 loans** from the Excel files in `data/`.

## API Endpoints

### 1. Register Customer
```
POST /api/register
```
**Request:**
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "age": 30,
  "monthly_income": 50000,
  "phone_number": 9876543210
}
```
**Response (201):**
```json
{
  "customer_id": 1,
  "name": "John Doe",
  "age": 30,
  "monthly_income": 50000,
  "approved_limit": 1800000,
  "phone_number": 9876543210
}
```

### 2. Check Loan Eligibility
```
POST /api/check-eligibility
```
**Request:**
```json
{
  "customer_id": 1,
  "loan_amount": 500000,
  "interest_rate": 10,
  "tenure": 24
}
```
**Response (200):**
```json
{
  "customer_id": 1,
  "approval": true,
  "interest_rate": 10,
  "corrected_interest_rate": 10,
  "tenure": 24,
  "monthly_installment": 23072.49
}
```

### 3. Create Loan
```
POST /api/create-loan
```
**Request:**
```json
{
  "customer_id": 1,
  "loan_amount": 500000,
  "interest_rate": 10,
  "tenure": 24
}
```
**Response (201 if approved, 200 if rejected):**
```json
{
  "loan_id": 1,
  "customer_id": 1,
  "loan_approved": true,
  "message": "Loan approved",
  "monthly_installment": 23072.49
}
```

### 4. View Single Loan
```
GET /api/view-loan/<loan_id>
```
**Response (200):**
```json
{
  "loan_id": 1,
  "customer": {
    "id": 1,
    "first_name": "John",
    "last_name": "Doe",
    "phone_number": 9876543210,
    "age": 30
  },
  "loan_amount": 500000,
  "interest_rate": 10,
  "monthly_installment": 23072.49,
  "tenure": 24
}
```

### 5. View All Loans for a Customer
```
GET /api/view-loans/<customer_id>
```
**Response (200):**
```json
[
  {
    "loan_id": 1,
    "loan_amount": 500000,
    "interest_rate": 10,
    "monthly_installment": 23072.49,
    "repayments_left": 20
  }
]
```

## Running Tests

```bash
docker-compose exec web python manage.py test
```

## Project Structure

```
credit_approval_system/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env
├── manage.py
├── core/              # Django project config
├── customers/         # Customer registration
├── loans/             # Loan eligibility, creation, viewing
├── ingestion/         # Background data ingestion (Celery)
└── data/
    ├── customer_data.xlsx
    └── loan_data.xlsx
```

## Credit Score Algorithm

The credit score is calculated out of **100 points** across 4 components:

| Component | Weight | Description |
|-----------|--------|-------------|
| Past loans paid on time | 30 pts | Average ratio of EMIs paid on time vs tenure |
| Number of loans | 25 pts | Fewer loans = higher score |
| Current year activity | 20 pts | Fewer new loans this year = higher score |
| Loan volume vs limit | 25 pts | Lower utilisation = higher score |

**Override:** If active loan amounts exceed the customer's approved limit, the credit score is forced to **0**.
