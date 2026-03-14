# Mini Jira Ticket System

A **Mini Jira–style ticket system** with **full observability and load-tested performance**.

**Stack:** React + FastAPI + PostgreSQL + Prometheus + Loki + Tempo + OpenTelemetry + Grafana

---

# 📹 Project Overview Video

▶ Watch the demo video on GitHub:

https://github.com/Rohit-Kombee/Mini-Jira-Ticket-System/blob/master/Project%20Overview.mp4

---

# 🚀 Load Testing Results (k6)

The system was tested using **k6 load testing** against the full stack (FastAPI API + PostgreSQL + Observability stack).

## Test Configuration

- Ramp to **20 VUs (10s)**
- Sustain **20 VUs (2m)**
- Spike to **50 VUs (10s)**
- Hold **50 VUs (30s)**
- Ramp down **10s**

**Max Virtual Users:** 50  
**Total Duration:** ~3 minutes

---

# Performance Results

| Metric | Result |
|------|------|
| Total Requests | **7,326** |
| Iterations | **4,659** |
| Error Rate | **0.00%** |
| Avg Latency | **94.75 ms** |
| Median Latency | **13.93 ms** |
| p90 Latency | **290 ms** |
| p95 Latency | **383.91 ms** |
| Max Latency | **2.39 s** |

---

# Thresholds

| Threshold | Target | Result |
|----------|--------|--------|
| Error Rate | `< 20%` | **0.00% ✓** |
| p95 Latency | `< 3000 ms` | **383 ms ✓** |

---

# Functional Checks

All functional checks passed successfully.

| Check | Result |
|-----|------|
| Login | ✓ |
| Create Ticket | ✓ |
| List Tickets | ✓ |
| Health Endpoint | ✓ |

**Checks Summary**

- Total Checks: **7,325**
- Success Rate: **100%**
- Failures: **0**

---

# Observability Metrics After Load Test (Grafana)

| Metric | Value |
|------|------|
| Request Rate | ~1.49K req/min |
| Error Rate | **0%** |
| API p95 Latency | ~448 ms |
| Logins (1h) | 4,254 |
| Tickets Created (1h) | 4,250 |

The system maintained **stable performance under load with zero errors and sub-400 ms p95 latency**.

---

# Project Overview

A **Mini Jira–style support ticket system** with built-in **observability**.

Users can:

- Login and manage tickets
- Assign developers or QA
- Track ticket status and priority
- Add messages to tickets

Admins manage users and assignments.

Observability tools monitor:

- **Metrics (Prometheus)**
- **Logs (Loki)**
- **Distributed Traces (Tempo)**

All services run via **Docker Compose**.

---

# Quick Start

```bash
docker compose up
```

### Services

| Service | URL |
|------|------|
| Frontend | http://localhost:5174 |
| API | http://localhost:8000 |
| Grafana | http://localhost:3000 |
| Prometheus | http://localhost:9090 |

Grafana login:

```
admin / admin
```

---

# Run Frontend Locally (Dev Mode)

Run backend stack first:

```bash
docker compose up backend postgres prometheus loki tempo otel-collector promtail grafana
```

Run frontend:

```bash
cd frontend
npm install
npm run dev
```

Open:

```
http://localhost:5173
```

---

# Default Admin

A default admin user is created on first run.

```
email: admin
password: admin
```

There is **no self-registration**.  
Only the **admin can create users**.

---

# Application Features

| Feature | Description |
|------|------|
| Authentication | JWT login/logout |
| User Management | Admin can create/update/delete users |
| Ticket Management | Create, list, update tickets |
| Assignments | Admin assigns Developer or QA |
| Messages | Comment system on tickets |
| Filters | Status, priority, creator, assignee |

---

# Roles & Permissions

## Admin
- Create tickets
- Assign users
- Manage users
- Full CRUD access

## Developer
- View assigned tickets
- Add messages
- Update ticket description

## QA
- View assigned tickets
- Add messages
- Update ticket status

---

# Tech Stack

| Layer | Technology |
|------|------|
| Frontend | React 18, Vite, TypeScript |
| Backend | FastAPI, Python |
| Database | PostgreSQL |
| Metrics | Prometheus |
| Logs | Loki + Promtail |
| Tracing | Tempo + OpenTelemetry |
| Visualization | Grafana |
| Load Testing | k6 |
| Containerization | Docker Compose |

---

# API Endpoints

## Auth

```
POST /auth/login
POST /auth/logout
GET /auth/me
```

## Users (Admin)

```
GET /users
POST /users
GET /users/{id}
PATCH /users/{id}
DELETE /users/{id}
```

## Tickets

```
POST /tickets
GET /tickets
GET /tickets/{id}
PATCH /tickets/{id}
```

## Messages

```
POST /tickets/{id}/messages
GET /tickets/{id}/messages
```

## Observability

```
GET /metrics
GET /health
```

---

# Project Structure

```
project-root/
  frontend/
  backend/
  config/
  loadtest/
  scripts/
  docker-compose.yml
```

---

# License

MIT
