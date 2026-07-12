# TrendAI Chatbot — Solutions Architect Lab

A minimal but production-shaped chatbot: browser UI → API → LLM → MongoDB,
running on Kubernetes (k3s) in AWS, with daily backups to S3 and a
security-gated CI/CD pipeline.

## Architecture
```
                 Internet
                    │  HTTP :80
              ┌─────▼─────┐
              │  Ingress  │  (Traefik on k3s)
              └─────┬─────┘
              ┌─────▼─────┐      ┌──────────────┐
              │ Frontend  │      │   Backend    │  POST /api/chat
              │  (nginx)  │─────▶│  (FastAPI)   │──────────────▶ Anthropic LLM
              └───────────┘      └──────┬───────┘
                                        │  27017 (NetworkPolicy-restricted)
                                 ┌──────▼───────┐
                                 │   MongoDB    │
                                 └──────┬───────┘
                                        │  mongodump (daily CronJob)
                                 ┌──────▼───────┐
                                 │   S3 bucket  │  (versioned, encrypted, private)
                                 └──────────────┘
```

## Repo map
| Path | Purpose |
|------|---------|
| `backend/` | FastAPI service, `POST /api/chat`, Mongo + LLM |
| `frontend/` | Static chat UI served by nginx |
| `k8s/` | Namespace, deployments, services, ingress, NetworkPolicy, backup CronJob |
| `terraform/` | VPC, subnets, EC2 (k3s), S3 bucket, least-privilege IAM |
| `.github/workflows/deploy.yml` | Gitleaks + ruff + Trivy, then build & deploy |
| `SETUP.md` | Step-by-step runbook |

## Security controls built in
- **Network segmentation:** NetworkPolicy lets only the backend reach MongoDB.
- **Secrets management:** credentials in K8s Secrets, never in Git (`secrets.example.yaml` is a template).
- **Least-privilege IAM:** node role can only `PutObject`/`ListBucket` on the backup bucket.
- **Hardened containers:** non-root, read-only root filesystem, no privilege escalation, resource limits.
- **CI/CD gates:** secret scan, dependency/CVE scan, and lint must run before deploy.
- **Encrypted, versioned, private S3** for backups.

See the presentation for the full security gap analysis.
