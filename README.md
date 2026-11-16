# Sales Ninja — AI-powered Sales Intelligence

Sales Ninja is a full-stack sales analytics application with transaction management, CSV ingestion, KPI dashboards, and an AI sales copilot powered by **Amazon Bedrock**.

> **Amazon Q clarification:** Amazon Q Business is a separately provisioned product with its own subscription and integration model. This repository implements the AWS-native Amazon Bedrock Converse API for the conversational AI layer. This gives the application a direct, configurable Amazon foundation-model integration. It does not claim to be an Amazon Q Business connector.

## Features

- Executive dashboard: revenue, profit, order count, customers, monthly revenue, top products.
- Sales management: list, create, delete and import CSV transactions.
- CSV validation, duplicate order handling, file size limit and row-level skip reporting.
- AI copilot: asks Amazon Bedrock using a compact sales snapshot; no arbitrary SQL generation or database write tools are exposed to the model.
- SQLite for quick local setup; PostgreSQL supported through SQLAlchemy.
- FastAPI OpenAPI docs, health endpoint and pytest API tests.
- Responsive React dashboard.

## Architecture

```text
Browser (React + Vite)
    | HTTP / JSON
    v
FastAPI REST API  ----------------------> Amazon Bedrock Runtime
    |                                      Converse API
    v
SQLAlchemy ORM
    |
    +---- SQLite (local default)
    |
    +---- PostgreSQL (deployment option)
```

The chat route calculates a server-side snapshot (KPIs, monthly trend, top products and regions) and sends that bounded context to Bedrock. The model is instructed to answer only from this snapshot. It cannot execute SQL, alter sales, or access arbitrary customer records.

## Requirements

- Python 3.11+
- Node.js 20+ and npm
- AWS account with Amazon Bedrock model access enabled in the selected region (only needed for live AI chat)
- Optional: PostgreSQL 15+

## Quick start

Run the backend and frontend in two terminals.

### 1. Configure environment

From the project root:

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

The defaults use SQLite and are enough to run the dashboard and sales APIs. The AI endpoint requires AWS credentials and Bedrock model access.

### 2. Backend

```bash
cd backend
python -m venv .venv
```

Activate the environment:

macOS/Linux:
```bash
source .venv/bin/activate
```

Windows PowerShell:
```powershell
.venv\Scripts\Activate.ps1
```

Install and start:
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

API: http://localhost:8000  
Swagger docs: http://localhost:8000/docs  
Health: http://localhost:8000/api/health

### 3. Frontend

In a second terminal, from the project root:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173.

If the API is hosted at a different URL, create `frontend/.env.local`:

```dotenv
VITE_API_URL=http://localhost:8000
```

Restart Vite after changing environment variables.

## Configure Amazon Bedrock

1. In AWS Console, choose the region you intend to use (default in this sample: `ap-south-1`).
2. Open Amazon Bedrock and enable/request access to a model available in that region. Model availability and access procedures vary by account and region.
3. Ensure the IAM principal used by the application is allowed to invoke the selected model.
4. Configure credentials using one of the AWS SDK-supported methods.

Example least-privilege policy (replace the resource ARN with the exact model/inference-profile ARN used in your account):

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": ["bedrock:InvokeModel"],
    "Resource": "arn:aws:bedrock:ap-south-1::foundation-model/anthropic.claude-3-haiku-20240307-v1:0"
  }]
}
```

For local development, the AWS CLI profile method is convenient:

```bash
aws configure --profile sales-ninja
aws sts get-caller-identity --profile sales-ninja
```

Then set `AWS_PROFILE=sales-ninja` in `.env`. Alternatively, use environment variables or an IAM role (recommended in AWS hosting). Do not commit AWS access keys or `.env` to Git.

Environment variables:
- `AWS_REGION`: Bedrock region.
- `BEDROCK_MODEL_ID`: Bedrock model ID or supported inference profile ID.
- `AWS_PROFILE`: optional local AWS CLI profile. Blank uses the standard SDK credential chain.

If the selected model is unavailable in your region, change both region and model ID to a model enabled for your account. The application returns HTTP 503 with the AWS error when Bedrock is not configured or invocation fails; dashboard and sales CRUD remain usable.

## Load the sample dataset

From the dashboard, choose **Import CSV** and select `sample-data/sales_sample.csv`.

Required CSV headers:

```text
order_id,order_date,customer,product,category,region,quantity,unit_price,unit_cost
```

- Dates use ISO format `YYYY-MM-DD`.
- Monetary values are numeric, in your chosen currency (the sample dashboard formats INR).
- Duplicate order IDs and invalid rows are skipped and included in the skipped count.
- Upload size is capped by `MAX_UPLOAD_MB` (default 10 MB).

## Run tests

From `backend/` with the virtual environment active:

```bash
pytest -q
```

The tests use an isolated in-memory SQLite database and do not call AWS.

## PostgreSQL setup

Create a database and user, then install the PostgreSQL driver:

```bash
pip install "psycopg[binary]"
```

Set the root `.env`:

```dotenv
DATABASE_URL=postgresql+psycopg://salesninja:YOUR_PASSWORD@localhost:5432/salesninja
```

Restart the API. SQLAlchemy creates the `sales` table on startup. For production, use a managed migration workflow (Alembic) rather than relying on `create_all`.

## API reference

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Health check |
| GET | `/api/sales` | List sales |
| POST | `/api/sales` | Create a sale |
| DELETE | `/api/sales/{id}` | Delete a sale |
| POST | `/api/sales/upload` | Import CSV |
| GET | `/api/analytics/summary` | KPI summary |
| GET | `/api/analytics/monthly` | Monthly revenue and profit |
| GET | `/api/analytics/products` | Product revenue ranking |
| GET | `/api/analytics/regions` | Region revenue ranking |
| POST | `/api/chat` | Ask the Bedrock sales copilot |

Example chat request:

```json
{"question":"Which product has the highest revenue?"}
```

## Deployment notes

- **Frontend:** build with `npm run build`; deploy `frontend/dist` to Vercel or another static host. Set `VITE_API_URL` to the public API URL at build time.
- **Backend:** deploy the FastAPI app to a Python host/container service using `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Configure secrets and AWS IAM role credentials in the hosting environment.
- **Database:** use managed PostgreSQL for persistent production storage. Do not use local SQLite on ephemeral hosting disks.
- Update `CORS_ORIGINS` to the exact deployed frontend origin(s).
- Keep AWS credentials in a secret manager or workload IAM role; never put them in frontend variables.
- Add authentication, authorization, rate limiting, audit logs, backups, migrations and monitoring before exposing this MVP to real customer data.

## Project structure

```text
sales-ninja/
├── backend/
│   ├── app/
│   │   ├── analytics.py
│   │   ├── bedrock.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── main.py
│   │   ├── models.py
│   │   └── schemas.py
│   ├── tests/
│   │   ├── conftest.py
│   │   └── test_api.py
│   └── requirements.txt
├── frontend/
│   ├── src/App.jsx
│   ├── src/main.jsx
│   ├── src/style.css
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── sample-data/sales_sample.csv
├── .env.example
└── README.md
```

## Known MVP limitations

- No login, user roles or tenant isolation yet. Do not use with sensitive production sales data until these are added.
- Chat answers are grounded in aggregate summaries, not every individual row; highly granular questions may not be answerable.
- No automated scheduled reports or email delivery.
- Currency formatting is INR in the UI; keep uploaded monetary data in one consistent currency.
- Bedrock model IDs, regional availability, model access and pricing are controlled by AWS and may change.
- The UI uses Google Fonts from a CDN; system fonts remain the fallback if offline.

## License

Provided as a starter project. Add your organization's license and notices before redistribution.
