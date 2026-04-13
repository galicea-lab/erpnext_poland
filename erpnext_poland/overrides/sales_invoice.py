# erpnext_poland/overrides/sales_invoice.py
import frappe
from frappe import _

import frappe

def fix_correction_invoice(doc, method):
    if not doc.is_return:
        return
    
    has_positive = any(item.amount > 0 for item in doc.items)
    frappe.logger().debug(f"[PL Korekta] is_return={doc.is_return}, has_positive={has_positive}")
    
    if not has_positive:
        return
    
    before = [u.get("target_ref_field") for u in doc.status_updater]
    
    for updater in doc.status_updater:
        updater.pop("target_ref_field", None)
    
    after = [u.get("target_ref_field") for u in doc.status_updater]
    frappe.logger().debug(f"[PL Korekta] target_ref_field before={before}, after={after}")
    

def fix_gl_for_storno(doc, method):
    """
    Przekształca wpisy GL z 'odwrócone strony' na 'ujemne kwoty po tej samej stronie'
    (storno czerwone / ujemne).
    """
    if not doc.is_return:
        return
    
    has_positive = any(item.amount > 0 for item in doc.items)
    # Możesz też zastosować dla KAŻDEJ korekty, nie tylko mieszanych
    
    gl_entries = frappe.get_all(
        "GL Entry",
        filters={
            "voucher_type": "Sales Invoice",
            "voucher_no": doc.name,
            "is_cancelled": 0,
        },
        fields=["name", "debit", "credit", "account"],
    )
    
    for entry in gl_entries:
        if entry.debit != 0 or entry.credit != 0:
            # Zamień: debit=100,credit=0  →  debit=0,credit=-100  (storno)
            new_debit  = -entry.credit  if entry.credit != 0 else 0
            new_credit = -entry.debit   if entry.debit  != 0 else 0
            
            frappe.db.set_value("GL Entry", entry.name, {
                "debit":  new_debit,
                "credit": new_credit,
            })
    
    frappe.db.commit()