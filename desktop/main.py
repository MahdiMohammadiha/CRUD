import sys
import requests
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QFrame,
    QDialog,
    QFormLayout,
    QLineEdit,
    QDialogButtonBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor, QBrush


API_BASE_URL = "http://127.0.0.1:8000"


class EditDialog(QDialog):
    def __init__(
        self, table_name: str, schema: list, row_data: dict = None, parent=None
    ):
        """
        Dialog for adding or editing a record.
        If row_data is None, it means add mode (empty form).
        """
        super().__init__(parent)
        self.setWindowTitle("Edit Record" if row_data else "Add Record")
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        self.table_name = table_name
        self.schema = schema
        self.row_data = row_data or {}
        self.inputs = {}

        layout = QFormLayout()

        pk_column = schema[0][0] if schema else None

        for col_name, col_type in schema:
            # For add mode, disable PK input if it exists (assuming auto-increment)
            if row_data is None and col_name == pk_column:
                continue

            value = self.row_data.get(col_name, "")
            field = QLineEdit(str(value))
            self.inputs[col_name] = field
            layout.addRow(f"{col_name} ({col_type})", field)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def get_data(self):
        """Collect input data as a dictionary"""
        return {col: field.text() for col, field in self.inputs.items()}


class TableViewer(QWidget):
    def __init__(self, table_name: str):
        super().__init__()
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        self.table_name = table_name
        self.schema = []
        self.pk_column = None

        self.layout = QVBoxLayout()

        # Add Record button
        self.add_button = QPushButton("Add Record")
        self.add_button.clicked.connect(self.add_record)
        self.layout.addWidget(self.add_button)

        self.table = QTableWidget()
        self.layout.addWidget(self.table)
        self.setLayout(self.layout)

        self.refresh()

    def refresh(self):
        schema_url = f"{API_BASE_URL}/api/tables/{self.table_name}/schema"
        data_url = f"{API_BASE_URL}/api/tables/{self.table_name}"
        pk_url = f"{API_BASE_URL}/api/tables/{self.table_name}/pk"

        schema_res = requests.get(schema_url)
        data_res = requests.get(data_url)
        pk_res = requests.get(pk_url)

        if not schema_res.ok or not data_res.ok or not pk_res.ok:
            QMessageBox.critical(
                self, "Error", f"Failed to load table: {self.table_name}"
            )
            return

        self.schema = schema_res.json()
        data = data_res.json()
        self.pk_column = pk_res.json()

        self.table.setColumnCount(len(self.schema) + 2)  # +1 Edit, +1 Delete
        self.table.setRowCount(len(data))

        headers = []
        for col, col_type in self.schema:
            if col == self.pk_column:
                headers.append(f"{col} (PK)")
            else:
                headers.append(col)
        headers += ["Edit", "Delete"]
        self.table.setHorizontalHeaderLabels(headers)

        for row_idx, row in enumerate(data):
            row_dict = dict(zip([col[0] for col in self.schema], row))

            for col_idx, value in enumerate(row):
                item = QTableWidgetItem(str(value))
                col_name = self.schema[col_idx][0]

                # Highlight PK column
                if col_name == self.pk_column:
                    font = QFont()
                    font.setBold(True)
                    item.setFont(font)
                    item.setForeground(QBrush(QColor("darkblue")))

                # Alternate row color
                if row_idx % 2 == 1:
                    item.setBackground(QBrush(QColor("#f0f0f0")))

                self.table.setItem(row_idx, col_idx, item)

            # Edit button
            edit_btn = QPushButton("Edit")
            edit_btn.clicked.connect(lambda _, r=row_dict: self.edit_record(r))
            self.table.setCellWidget(row_idx, len(self.schema), edit_btn)

            # Delete button
            delete_btn = QPushButton("Delete")
            delete_btn.clicked.connect(lambda _, r=row_dict: self.confirm_delete(r))
            self.table.setCellWidget(row_idx, len(self.schema) + 1, delete_btn)

        self.table.resizeColumnsToContents()

    def add_record(self):
        """Open dialog in add mode"""
        dialog = EditDialog(self.table_name, self.schema, row_data=None, parent=self)
        if dialog.exec():
            new_data = dialog.get_data()
            url = f"{API_BASE_URL}/api/tables/{self.table_name}"
            res = requests.post(url, json=new_data)
            if res.ok:
                self.refresh()
            else:
                QMessageBox.critical(self, "Error", f"Failed to add record: {res.text}")

    def confirm_delete(self, row_dict):
        pk_value = row_dict.get(self.pk_column)
        msg = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete record #{pk_value}?",
        )
        if msg == QMessageBox.StandardButton.Yes:
            self.delete_record(pk_value)

    def delete_record(self, pk_value):
        delete_url = f"{API_BASE_URL}/api/tables/{self.table_name}/{pk_value}"
        res = requests.delete(delete_url)
        if res.ok:
            self.refresh()
        else:
            QMessageBox.critical(self, "Error", f"Failed to delete record: {res.text}")

    def edit_record(self, row_dict):
        dialog = EditDialog(self.table_name, self.schema, row_dict, self)
        if dialog.exec():
            new_data = dialog.get_data()
            pk_value = row_dict.get(self.pk_column)
            url = f"{API_BASE_URL}/api/tables/{self.table_name}/{pk_value}"
            res = requests.put(url, json=new_data)
            if res.ok:
                self.refresh()
            else:
                QMessageBox.critical(
                    self, "Error", f"Failed to update record: {res.text}"
                )


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dynamic CRUD UI")
        self.resize(900, 600)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.main_layout = QVBoxLayout()
        self.central_widget.setLayout(self.main_layout)

        # Navbar
        self.navbar_frame = QFrame()
        self.navbar_layout = QHBoxLayout()
        self.navbar_frame.setLayout(self.navbar_layout)
        self.main_layout.addWidget(self.navbar_frame)

        # Table container
        self.table_container = QWidget()
        self.table_layout = QVBoxLayout()
        self.table_container.setLayout(self.table_layout)
        self.main_layout.addWidget(self.table_container)

        self.load_tables()

    def load_tables(self):
        res = requests.get(f"{API_BASE_URL}/api/tables")
        if not res.ok:
            QMessageBox.critical(self, "Error", "Failed to load tables")
            return

        tables = res.json()

        for tbl in tables:
            btn = QPushButton(tbl["table"])
            btn.clicked.connect(lambda _, t=tbl["table"]: self.load_table_data(t))
            self.navbar_layout.addWidget(btn)

    def load_table_data(self, table_name: str):
        for i in reversed(range(self.table_layout.count())):
            widget = self.table_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        viewer = TableViewer(table_name)
        self.table_layout.addWidget(viewer)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
