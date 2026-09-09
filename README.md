# 📦 StockFW: Intelligent Warehouse Operating System

> **A modern, full-stack inventory platform that tracks stock movements in real time, automatically predicts when to reorder supplies, and uses Machine Learning to detect inventory shrinkage and theft.**

[![CI/CD Pipeline](https://github.com/mrmarquito/stockfw/actions/workflows/ci.yml/badge.svg)](https://github.com/mrmarquito/stockfw/actions)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI%20(Python%203.12)-009688.svg?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL%2016-4169E1.svg?style=flat&logo=postgresql)](https://www.postgresql.org/)
[![Flutter](https://img.shields.io/badge/Frontend-Flutter%203.x-02569B.svg?style=flat&logo=flutter)](https://flutter.dev)
[![Docker](https://img.shields.io/badge/Deploy-Docker%20Compose-2496ED.svg?style=flat&logo=docker)](https://docker.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 💡 What is StockFW?

Warehouses often struggle with three major headaches:
1. **Lost inventory** during bin-to-bin transfers.
2. **Stockouts & overordering** caused by human error in reorder calculations.
3. **Unexplained missing inventory (shrinkage)** occurring during off-hours.

**StockFW** solves this with an integrated, automated platform:
* **For Floor Workers:** A high-contrast mobile/web scanner interface designed for fast-paced warehouse environments. Scan a bin, scan an item, enter the count, and the transfer is permanently logged.
* **For Warehouse Managers:** An autonomous replenishment brain. It monitors stock levels in real time and automatically creates draft Purchase Orders using the Economic Order Quantity (EOQ) formula before items run out.
* **For Loss Prevention:** An AI watchdog. An unsupervised Scikit-learn Machine Learning model continuously audits movement logs to flag abnormal movement sizes or suspicious weekend/nighttime activity.

---

## 🛠️ The Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Mobile & Web UI** | Flutter 3.x / Dart | Tactical scanner interface with live barcode scanning and offline fallback. |
| **API Engine** | FastAPI (Python 3.12) | High-performance async REST API with OAuth2 JWT token security. |
| **Database** | PostgreSQL 16 + Alembic | ACID-compliant relational ledger with versioned database migrations. |
| **Machine Learning** | Scikit-Learn (Isolation Forest) | Multidimensional anomaly detection for stock loss and theft prevention. |
| **Reverse Proxy** | Caddy v2 | Automated TLS (HTTPS) certificates, security headers, and CORS handling. |
| **Backups** | `postgres-backup-local` | Daily scheduled database dumps (`pg_dump`) with automated cleanup retention. |
| **Deployment** | Docker Compose & GHCR | Fully containerized deployment with zero-plaintext Docker secrets. |

---

## 🔄 How a Stock Transfer Works

```text
[ Warehouse Floor ]                    [ Backend Engine ]                  [ Audit & ML ]
  Worker Scans QR                        FastAPI Engine                     PostgreSQL Ledger
        │                                      │                                    │
        ├── 1. Scan Source Bin & SKU ─────────▶│                                    │
        │                                      ├── 2. Verify stock availability ───▶│
        │                                      │                                    │
        ├── 3. Confirm Quantity & Target ─────▶│                                    │
        │                                      ├── 4. Atomic balance deduction ────▶│
        │                                      │      and target credit             │
        │                                      │                                    │
        │◀── 5. Transfer Success Confirmed ────┤── 6. Isolation Forest AI checks ───┘
                                                      transfer for suspicious timing/volume
```

---

## 🚀 How to Run StockFW

You can run the entire production-grade stack (FastAPI, PostgreSQL, ML anomaly detection, and Caddy TLS reverse proxy) locally using Docker Compose, or run the Flutter scanning interface in your browser.

### 1. Prerequisites
* **Docker & Docker Compose:** Install [Docker Desktop](https://www.docker.com/products/docker-desktop/) (v24+ recommended).
* **OpenSSL:** Standard on macOS/Linux and Windows PowerShell for key generation.
* **Flutter SDK:** (Optional, only needed if modifying or running the scanner locally) [Flutter 3.x](https://docs.flutter.dev/get-started/install).

---

### 2. Full Stack Deployment (Docker Compose)

#### Step A: Generate Secure Passwords & Keys
The system uses Docker secrets so credentials are never exposed in plaintext[cite: 1]. Create the `secrets/` directory and generate two high-entropy keys[cite: 1]:

```bash
mkdir -p secrets
openssl rand -hex 24 > secrets/postgres_password.txt
openssl rand -hex 32 > secrets/app_secret_key.txt
chmod 600 secrets/*

```

#### Step B: Set Up Your Production Environment File

Create a `.env.prod` file in the project root directory:

```ini
GHCR_IMAGE_PATH=mrmarquito/stockfw
IMAGE_TAG=latest
DOMAIN_NAME=localhost
CORS_ORIGIN=*
POSTGRES_DB=warehouse_erp
POSTGRES_USER=erp_admin
WEB_CONCURRENCY=4
```

#### Step C: Build and Launch Containers

Run Docker Compose to boot the PostgreSQL database, FastAPI engine, Caddy gateway, and automated backup worker:

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build

```

Verify that all containers report healthy:

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod ps

```

#### Step D: Seed Initial Warehouse Data

Run the database migrations and seed baseline warehouse hubs, products, and bin allocations:

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod exec app python -m app.seed

```

---

### 3. Verify System Endpoints

Once the containers are running, test the core services directly in your browser or terminal:

* **Interactive API Documentation (Swagger):** Visit [`https://localhost/docs`](https://localhost/docs) to view and test all REST routes.


* **System Health Check:** Run `curl -k https://localhost/health` to check database connectivity.


* **AI Anomaly Audit:** Access [`https://localhost/api/v1/audit/anomalies`](https://localhost/api/v1/audit/anomalies) to trigger the Scikit-learn Isolation Forest model and detect potential shrinkage.



---

### 4. Running the Flutter Scanner UI

You can interact with the system using either the hosted web client or a local Flutter environment.

#### Option A: Hosted Web Client (GitHub Pages)

Visit the deployed web application at:

👉 **`https://mrmarquito.github.io/stockfw/`**

#### Option B: Run Locally via Flutter

```bash
cd mobile
flutter pub get
flutter run -d chrome --web-port=3000

```

#### Default Floor Worker Credentials

* **Gateway URL:** `https://localhost`
* **Username:** `floor_worker`

* **Password:** `FloorWorker123!`

---

### 5. Running the Automated Test Suite

To run the backend test suite in full database isolation:

```bash
# 1. Start a temporary test PostgreSQL instance
docker run -d --name erp-test-db -p 5432:5432 -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=warehouse_erp_test postgres:16-alpine

# 2. Run pytest across all inventory, PO, and ML test suites
pytest -v

# 3. Clean up the test container
docker rm -f erp-test-db

```

---

### 6. Managing Automated Backups

The `db-backup` sidecar automatically dumps the database to `/backups/daily` on a nightly schedule.

* **Trigger an immediate manual snapshot:**
```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod exec db-backup /backup.sh

```

* **List existing compressed archives:**
```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod exec db-backup ls -lh /backups/daily

```
