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
