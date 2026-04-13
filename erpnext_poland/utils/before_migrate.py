import frappe
import json
import os

def before_migrate_setup():
    """
    Funkcja wykonywana PRZED migracją i fixtures.
    Tutaj aktualizujemy payments_tab przed załadowaniem fixtures.
    """
    update_sales_invoice_tabs_before_fixtures()

def update_sales_invoice_tabs_before_fixtures():
    """
    Aktualizuje payments_tab PRZED załadowaniem fixtures
    """
    
    # Znajdź payments_tab
    payments_tab = frappe.db.get_value(
        "Custom Field",
        {"dt": "Sales Invoice", "fieldname": "payments_tab"},
        "name"
    )
    
    if payments_tab:
        # Ustaw next_tab na twoją nową zakładkę
        frappe.db.set_value(
            "Custom Field",
            payments_tab,
            "next_tab",
            "jpk_ksef_tab"  # nazwa twojej nowej zakładki z fixtures
        )
        frappe.db.commit()
