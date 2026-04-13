import frappe
from frappe.model.document import Document

def fetch_and_create_invoices():
    # 1. Pobierz dane z KSeF (logika autoryzacji i pobierania XML)
    raw_invoices = get_invoices_from_ksef_api() 

    for data in raw_invoices:
        try:
            create_purchase_invoice(data)
            frappe.db.commit() # Zatwierdzamy każdą fakturę z osobna
        except Exception as e:
            frappe.log_error(title="KSeF Import Error", message=frappe.get_traceback())

def create_purchase_invoice(ksef_data):
    # Tworzenie nowego dokumentu w pamięci
    doc = frappe.get_doc({
        "doctype": "Purchase Invoice",
        "supplier": map_nip_to_supplier(ksef_data['nip_sprzedawcy']),
        "posting_date": ksef_data['data_wystawienia'],
        "bill_no": ksef_data['numer_ksef'], # Numer KSeF warto trzymać w osobnym polu
        "currency": ksef_data['waluta'],
        "items": []
    })

    # Dodawanie pozycji faktury
    for item in ksef_data['pozycje']:
        doc.append("items", {
            "item_code": map_item(item['description']), # Mapowanie na indeksy ERPNext
            "qty": item['quantity'],
            "rate": item['net_price'],
            "uom": "Unit"
        })

    # Obliczenie podatków i sum (ERPNext zrobi to automatycznie przy insert/save)
    doc.insert()
    
    # Opcjonalnie: doc.submit() jeśli chcesz, by faktura była od razu zaksięgowana
    # Bez submit() trafi do "Draft" (Szkic)
