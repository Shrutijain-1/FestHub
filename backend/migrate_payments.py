"""One-time: adds the payment columns to an existing database without deleting data."""
from sqlalchemy import inspect, text

from backend.database import engine

COLUMNS = {
    "amount_paid": "FLOAT DEFAULT 0",
    "payment_status": "VARCHAR(20) DEFAULT 'not_required'",
    "payment_method": "VARCHAR(30)",
    "payment_reference": "VARCHAR(40)",
    "paid_at": "DATETIME",
    "refund_reference": "VARCHAR(40)",
    "refund_initiated_at": "DATETIME",
}

existing = {column["name"] for column in inspect(engine).get_columns("registrations")}
with engine.begin() as connection:
    for name, definition in COLUMNS.items():
        if name not in existing:
            connection.execute(text(f"ALTER TABLE registrations ADD COLUMN {name} {definition}"))
            print("Added column:", name)
print("Done.")