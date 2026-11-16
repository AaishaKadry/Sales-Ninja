# Security checklist before production

- Add authentication and authorization; scope every query to the authenticated tenant.
- Use a managed PostgreSQL database with TLS, backups and least-privilege credentials.
- Use IAM roles instead of long-lived AWS access keys.
- Restrict Bedrock invocation to approved model/inference-profile resources.
- Avoid sending personal/customer-identifying data to the model; current chat sends aggregate analytics only.
- Add request rate limits, audit logs, monitoring and alerting.
- Add Alembic migrations and automated dependency/security scanning.
- Set CORS to exact production origins.
- Store secrets in a secret manager; never in source control or Vite variables.
