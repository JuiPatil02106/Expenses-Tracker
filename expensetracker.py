import sqlite3
import pandas as pd
from tkinter import *
from tkinter import messagebox, ttk
from datetime import datetime
import matplotlib.pyplot as plt

# Database setup
conn = sqlite3.connect("expenses.db")
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    description TEXT NOT NULL,
    amount REAL NOT NULL,
    category TEXT NOT NULL,
    date TEXT NOT NULL
)
''')
conn.commit()

categories = ["Food", "Travel", "Shopping", "Bills", "Entertainment", "Other"]

# Functions
def add_expense():
    desc = desc_entry.get()
    amount = amount_entry.get()
    cat = category_combo.get()
    date = date_entry.get() or datetime.today().strftime('%Y-%m-%d')

    if not desc or not amount or not cat:
        messagebox.showerror("Error", "All fields except date are required.")
        return

    try:
        amount = float(amount)
        datetime.strptime(date, '%d-%m-%Y')  # Date validation
        cursor.execute("INSERT INTO expenses (description, amount, category, date) VALUES (?, ?, ?, ?)",
                       (desc, amount, cat, date))
        conn.commit()
        messagebox.showinfo("Success", "Expense added.")
        clear_entries()
        refresh_table()
    except ValueError:
        messagebox.showerror("Error", "Amount must be a number and date must be in DD-MM-YYYY format.")
    except Exception as e:
        messagebox.showerror("Error", f"Something went wrong: {e}")

def clear_entries():
    desc_entry.delete(0, END)
    amount_entry.delete(0, END) 
    category_combo.set('')
    date_entry.delete(0, END)

def refresh_table():
    for row in tree.get_children():
        tree.delete(row)
    cursor.execute("SELECT * FROM expenses")
    for row in cursor.fetchall():
        tree.insert("", END, values=row)

    # Summary Stats
    cursor.execute("SELECT SUM(amount), MAX(amount) FROM expenses")
    total, highest = cursor.fetchone()
    total = total or 0
    highest = highest or 0

    cursor.execute("SELECT strftime('%Y-%m', date) as month, SUM(amount) FROM expenses GROUP BY month")
    months_data = cursor.fetchall()
    monthly_avg = sum([m[1] for m in months_data]) / len(months_data) if months_data else 0

    total_label.config(text=f"Total: ₹{total:.2f}")
    highest_label.config(text=f"Highest: ₹{highest:.2f}")
    avg_label.config(text=f"Monthly Avg: ₹{monthly_avg:.2f}")

def export_to_excel():
    cursor.execute("SELECT * FROM expenses")
    data = cursor.fetchall()
    df = pd.DataFrame(data, columns=["ID", "Description", "Amount", "Category", "Date"])
    df.to_excel("expenses_export.xlsx", index=False)
    messagebox.showinfo("Exported", "Expenses exported to 'expenses_export.xlsx'.")

def show_graph():
    cursor.execute('''
        SELECT strftime('%Y-%m', date) as month, SUM(amount)
        FROM expenses GROUP BY month ORDER BY month
    ''')
    rows = cursor.fetchall()
    if not rows:
        messagebox.showwarning("No Data", "No data to display.")
        return

    months = [r[0] for r in rows]
    totals = [r[1] for r in rows]

    plt.bar(months, totals, color="salmon")
    plt.xlabel("Month")
    plt.ylabel("Total Expense")
    plt.title("Monthly Expense Summary")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

def search_expenses():
    query = search_entry.get().lower()
    for row in tree.get_children():
        tree.delete(row)

    cursor.execute("SELECT * FROM expenses")
    rows = cursor.fetchall()
    for row in rows:
        if (query in str(row[1]).lower() or
            query in str(row[2]).lower() or
            query in str(row[3]).lower() or
            query in str(row[4]).lower()):
            tree.insert("", END, values=row)

def delete_expense():
    selected_item = tree.selection()
    if not selected_item:
        messagebox.showwarning("No Selection", "Please select an expense to delete.")
        return

    confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this expense?")
    if not confirm:
        return

    expense_id = tree.item(selected_item[0])['values'][0]
    cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    conn.commit()
    tree.delete(selected_item[0])
    refresh_table()
    messagebox.showinfo("Deleted", "Expense deleted successfully.")

# GUI Setup
root = Tk()
root.title("Expense Tracker")
root.geometry("950x650")
root.configure(bg="#f5f5f5")

style = ttk.Style()
style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=6)
style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
style.configure("Treeview", rowheight=25)

# Input Fields
Label(root, text="Description", bg="#f5f5f5").grid(row=0, column=0, sticky=W, padx=10, pady=5)
desc_entry = Entry(root, width=30)
desc_entry.grid(row=0, column=1, pady=5)

Label(root, text="Amount", bg="#f5f5f5").grid(row=1, column=0, sticky=W, padx=10)
amount_entry = Entry(root, width=30)
amount_entry.grid(row=1, column=1, pady=5)

Label(root, text="Category", bg="#f5f5f5").grid(row=2, column=0, sticky=W, padx=10)
category_combo = ttk.Combobox(root, values=categories, state="readonly", width=28)
category_combo.grid(row=2, column=1, pady=5)

Label(root, text="Date (YYYY-MM-DD)", bg="#f5f5f5").grid(row=3, column=0, sticky=W, padx=10)
date_entry = Entry(root, width=30)
date_entry.grid(row=3, column=1, pady=5)

# Action Buttons
Button(root, text="Add Expense", command=add_expense).grid(row=4, column=0, pady=10, padx=10)
Button(root, text="Export to Excel", command=export_to_excel).grid(row=4, column=1, pady=10)
Button(root, text="Monthly Graph", command=show_graph).grid(row=4, column=2, pady=10)
Button(root, text="Delete Selected", command=delete_expense).grid(row=4, column=3, pady=10)

# Search
Label(root, text="Search", bg="#f5f5f5").grid(row=5, column=0, padx=10, sticky=W)
search_entry = Entry(root, width=40)
search_entry.grid(row=5, column=1, pady=5)
Button(root, text="Search", command=search_expenses).grid(row=5, column=2, padx=10)

# Expense Table
cols = ("ID", "Description", "Amount", "Category", "Date")
tree = ttk.Treeview(root, columns=cols, show='headings', height=15)
for col in cols:
    tree.heading(col, text=col)
    tree.column(col, anchor=W, width=130)
tree.grid(row=6, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")

# Summary Stats
summary_frame = LabelFrame(root, text="Summary", bg="#f5f5f5", padx=10, pady=5, font=("Segoe UI", 10, "bold"))
summary_frame.grid(row=7, column=0, columnspan=4, sticky="we", padx=10, pady=10)

total_label = Label(summary_frame, text="Total: ₹0.00", bg="#f5f5f5", font=("Segoe UI", 10, "bold"))
total_label.grid(row=0, column=0, padx=10)

highest_label = Label(summary_frame, text="Highest: ₹0.00", bg="#f5f5f5", font=("Segoe UI", 10, "bold"))
highest_label.grid(row=0, column=1, padx=10)

avg_label = Label(summary_frame, text="Monthly Avg: ₹0.00", bg="#f5f5f5", font=("Segoe UI", 10, "bold"))
avg_label.grid(row=0, column=2, padx=10)

refresh_table()

root.mainloop()
conn.close()
