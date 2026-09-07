# Warehouse ERP & Supply Chain Engine

A high-concurrency, data-integrity-first ERP inventory backend.

## Key Features
- **Pessimistic Concurrency**: Prevents stock balance races via `SELECT ... FOR UPDATE`.
- **Database-Level Invariants**: Relational constraints enforce non-negative balances.
- **Append-Only Movement Log**: Tamper-evident ledger for audits and ML tracking.

## Quickstart
1. Install dependencies:
   ```bash
   pip install -e .[dev]
