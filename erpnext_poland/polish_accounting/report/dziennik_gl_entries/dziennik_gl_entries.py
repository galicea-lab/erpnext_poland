import frappe
from frappe import _

def execute(filters=None):
    if not filters:
        filters = {}
    
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart_data(data, filters)
    
    return columns, data, None, chart

def get_columns():
    # ... jak wyżej
    pass

# Dodaj tę funkcję dla opcjonalnego wykresu
def get_chart_data(data, filters):
    if not data:
        return None
    
    # Suma debetów i kredytów według dziennika
    dziennik_summary = {}
    
    for row in data:
        dziennik = row.get("dziennik") or _("Brak dziennika")
        if dziennik not in dziennik_summary:
            dziennik_summary[dziennik] = {"debit": 0, "credit": 0}
        
        dziennik_summary[dziennik]["debit"] += row.get("debit", 0)
        dziennik_summary[dziennik]["credit"] += row.get("credit", 0)
    
    return {
        "data": {
            "labels": list(dziennik_summary.keys()),
            "datasets": [
                {
                    "name": _("Debit"),
                    "values": [dziennik_summary[d]["debit"] for d in dziennik_summary]
                },
                {
                    "name": _("Credit"),
                    "values": [dziennik_summary[d]["credit"] for d in dziennik_summary]
                }
            ]
        },
        "type": "bar"
    }



def get_columns():
    return [
        {
            "fieldname": "posting_date",
            "label": _("Posting Date"),
            "fieldtype": "Date",
            "width": 100
        },
        {
            "fieldname": "voucher_type",
            "label": _("Voucher Type"),
            "fieldtype": "Data",
            "width": 120
        },
        {
            "fieldname": "voucher_no",
            "label": _("Voucher No"),
            "fieldtype": "Dynamic Link",
            "options": "voucher_type",  # To sprawia, że link jest klikalny
            "width": 150
        },
        {
            "fieldname": "account",
            "label": _("Account"),
            "fieldtype": "Link",
            "options": "Account",
            "width": 200
        },
        {
            "fieldname": "party_type",
            "label": _("Party Type"),
            "fieldtype": "Data",
            "width": 100
        },
        {
            "fieldname": "party",
            "label": _("Party"),
            "fieldtype": "Dynamic Link",
            "options": "party_type",
            "width": 150
        },
        {
            "fieldname": "debit",
            "label": _("Debit"),
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "fieldname": "credit",
            "label": _("Credit"),
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "fieldname": "against",
            "label": _("Against"),
            "fieldtype": "Data",
            "width": 150
        },
        {
            "fieldname": "remarks",
            "label": _("Remarks"),
            "fieldtype": "Text",
            "width": 200
        },
        {
            "fieldname": "dziennik",
            "label": _("Dziennik"),
            "fieldtype": "Link",
            "options": "dziennik_definicja",
            "width": 120
        }
    ]

def get_data(filters):
    conditions = get_conditions(filters)
    
    data = frappe.db.sql(f"""
        SELECT
            posting_date,
            voucher_type,
            voucher_no,
            account,
            party_type,
            party,
            debit,
            credit,
            against,
            remarks,
            dziennik
        FROM `tabGL Entry`
        WHERE docstatus < 2
        {conditions}
        ORDER BY posting_date DESC, creation DESC
    """, filters, as_dict=1)
    
    return data

def get_conditions(filters):
    conditions = []
    
    if filters.get("company"):
        conditions.append("company = %(company)s")
    
    if filters.get("from_date"):
        conditions.append("posting_date >= %(from_date)s")
    
    if filters.get("to_date"):
        conditions.append("posting_date <= %(to_date)s")
    
    if filters.get("dziennik"):
        conditions.append("dziennik = %(dziennik)s")
    
    if filters.get("account"):
        conditions.append("account = %(account)s")
    
    if filters.get("voucher_type"):
        conditions.append("voucher_type = %(voucher_type)s")
    
    return " AND " + " AND ".join(conditions) if conditions else ""

