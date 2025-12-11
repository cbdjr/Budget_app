# main.py
import sys
import threading
import requests
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QTableWidget, QTableWidgetItem, QMessageBox
)
from PySide6.QtCore import Qt
from backend import create_app

API_URL = "http://127.0.0.1:5000/api"

# ---- Start Flask server in background ----
def run_flask():
    app = create_app()
    app.run(port=5000, debug=False, use_reloader=False)

flask_thread = threading.Thread(target=run_flask, daemon=True)
flask_thread.start()

# ---- PySide GUI ----
class BudgetApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Budgeting App")
        self.resize(700, 500)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Input form
        form_layout = QHBoxLayout()
        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText("Description")
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("Amount")
        self.cat_input = QLineEdit()
        self.cat_input.setPlaceholderText("Category")
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self.add_expense)
        form_layout.addWidget(self.desc_input)
        form_layout.addWidget(self.amount_input)
        form_layout.addWidget(self.cat_input)
        form_layout.addWidget(add_btn)
        layout.addLayout(form_layout)

        # Table
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Description", "Category", "Amount", "Time"]
        )
        self.table.setColumnHidden(0, True)
        layout.addWidget(self.table)

        # Buttons
        btn_layout = QHBoxLayout()
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_expenses)
        delete_btn = QPushButton("Delete Selected")
        delete_btn.clicked.connect(self.delete_selected)
        btn_layout.addWidget(refresh_btn)
        btn_layout.addWidget(delete_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.load_expenses()

    def load_expenses(self):
        try:
            r = requests.get(f"{API_URL}/expenses", timeout=2)
            r.raise_for_status()
            expenses = r.json()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not load expenses:\n{e}")
            return
        self.table.setRowCount(0)
        for exp in expenses:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(exp["id"])))
            self.table.setItem(row, 1, QTableWidgetItem(exp["description"]))
            self.table.setItem(row, 2, QTableWidgetItem(exp["category"]))
            self.table.setItem(row, 3, QTableWidgetItem(f"${exp['amount']:.2f}"))
            self.table.setItem(row, 4, QTableWidgetItem(exp["created_at"]))

    def add_expense(self):
        desc = self.desc_input.text().strip()
        amt = self.amount_input.text().strip()
        cat = self.cat_input.text().strip() or "Uncategorized"
        if not desc or not amt:
            QMessageBox.information(self, "Input", "Enter description and amount")
            return
        try:
            float(amt)
        except:
            QMessageBox.information(self, "Input", "Amount must be a number")
            return
        try:
            r = requests.post(f"{API_URL}/expenses",
                              json={"description": desc, "amount": amt, "category": cat},
                              timeout=2)
            r.raise_for_status()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not add expense:\n{e}")
            return
        self.desc_input.clear()
        self.amount_input.clear()
        self.cat_input.clear()
        self.load_expenses()

    def delete_selected(self):
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.information(self, "Select", "Select a row to delete")
            return
        row = selected[0].row()
        exp_id = self.table.item(row, 0).text()
        confirm = QMessageBox.question(self, "Confirm", "Delete this expense?")
        if confirm != QMessageBox.StandardButton.Yes:
            return
        try:
            r = requests.delete(f"{API_URL}/expenses/{exp_id}", timeout=2)
            r.raise_for_status()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not delete:\n{e}")
            return
        self.load_expenses()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BudgetApp()
    window.show()
    sys.exit(app.exec())
