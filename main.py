from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from uuid import uuid4
import sqlite3

app = FastAPI()

# Database setup
conn = sqlite3.connect("expenses.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS expenses (
    txn_id TEXT PRIMARY KEY,
    group_id TEXT NOT NULL,
    description TEXT,
    amount REAL NOT NULL,
    paid_by TEXT NOT NULL
)
""")
conn.commit()

# Data model for requests
class Expense(BaseModel):
    group_id: str
    description: Optional[str] = None
    amount: float
    paid_by: str

class ExpenseUpdate(BaseModel):
    description: Optional[str] = None
    amount: Optional[float] = None
    paid_by: Optional[str] = None

@app.get("/")
def greet_users():
    return "Hello! Welcome to Settleup."

@app.post("/expenses/add")
def add_expense(expense: Expense):
    expense_id = str(uuid4())
    cursor.execute(
        "INSERT INTO expenses (txn_id, group_id, description, amount, paid_by) VALUES (?, ?, ?, ?, ?)",
        (expense_id, expense.group_id, expense.description, expense.amount, expense.paid_by)
    )
    conn.commit()
    return {"message": "Expense added successfully", "expense_id": expense_id}

@app.put("/expenses/{expense_id}")
def modify_expense(expense_id: str, expense: ExpenseUpdate):
    cursor.execute("SELECT * FROM expenses WHERE txn_id = ?", (expense_id,))
    if cursor.fetchone() is None:
        raise HTTPException(status_code=404, detail="Expense not found")

    # Build update query dynamically
    fields = []
    values = []
    for key, value in expense.dict(exclude_unset=True).items():
        fields.append(f"{key} = ?")
        values.append(value)
    values.append(expense_id)

    cursor.execute(f"UPDATE expenses SET {', '.join(fields)} WHERE txn_id = ?", values)
    conn.commit()
    return {"message": "Expense updated successfully"}

@app.get("/expenses/{expense_id}")
def get_expense(expense_id: str):
    cursor.execute("SELECT * FROM expenses WHERE txn_id = ?", (expense_id,))
    row = cursor.fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Expense not found")

    expense = {
        "txn_id": row[0],
        "group_id": row[1],
        "description": row[2],
        "amount": row[3],
        "paid_by": row[4]
    }
    return expense

@app.get("/expenses/")
def get_expenses(group_id: Optional[str] = Query(None), paid_by: Optional[str] = Query(None)):
    query = "SELECT * FROM expenses WHERE 1=1"
    params = []

    if group_id:
        query += " AND group_id = ?"
        params.append(group_id)
    if paid_by:
        query += " AND paid_by = ?"
        params.append(paid_by)

    cursor.execute(query, params)
    rows = cursor.fetchall()

    expenses = [{
        "txn_id": row[0],
        "group_id": row[1],
        "description": row[2],
        "amount": row[3],
        "paid_by": row[4]
    } for row in rows]

    return {"expenses": expenses}