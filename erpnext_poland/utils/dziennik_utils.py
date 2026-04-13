import frappe

@frappe.whitelist()
def get_dziennik_for_voucher(voucher_type, entry_type=None):
    """
    Znajduje odpowiedni dziennik na podstawie voucher_type i opcjonalnie entry_type
    """
    filters = {
        "docstatus": 1  # tylko zatwierdzone definicje
    }
    
    dzienniki = frappe.get_all(
        "dziennik_definicja",
        filters=filters,
        fields=["name", "kod"]
    )
    
    for dziennik in dzienniki:
        # Pobierz dozwolone voucher types
        allowed_vouchers = frappe.get_all(
            "select_voucher_type",
            filters={"parent": dziennik.name},
            fields=["voucher_type"]
        )
        
        voucher_types_list = [v.voucher_type for v in allowed_vouchers]
        
        # Jeśli to Journal Entry, sprawdź także entry_type
        if voucher_type == "Journal Entry" and entry_type:
            allowed_entries = frappe.get_all(
                "select_entry_type",
                filters={"parent": dziennik.name},
                fields=["entry_type"]
            )
            entry_types_list = [e.entry_type for e in allowed_entries]
            
            if voucher_type in voucher_types_list and entry_type in entry_types_list:
                return dziennik.kod # name
        
        # Dla innych typów dokumentów
        elif voucher_type in voucher_types_list:
            return dziennik.kod # name
    
    return None


def set_dziennik_for_gl_entries(doc, method=None):
    """
    Ustawia dziennik dla wszystkich GL Entry związanych z dokumentem
    """
    voucher_type = doc.doctype
    entry_type = getattr(doc, "voucher_type", None)  # dla Journal Entry
    
    dziennik = get_dziennik_for_voucher(voucher_type, entry_type)
    
    if dziennik:
        # Aktualizuj istniejące GL Entry
        frappe.db.sql("""
            UPDATE `tabGL Entry`
            SET dziennik = %s
            WHERE voucher_type = %s AND voucher_no = %s
        """, (dziennik, voucher_type, doc.name))
        
        frappe.db.commit()


def set_dziennik_on_gl_entry(doc, method=None):
    """
    Automatycznie ustawia dziennik podczas tworzenia GL Entry
    """
    if not doc.dziennik:
        # Pobierz źródłowy dokument
        source_doc = frappe.get_doc(doc.voucher_type, doc.voucher_no)
        entry_type = getattr(source_doc, "voucher_type", None)
        
        dziennik = get_dziennik_for_voucher(doc.voucher_type, entry_type)
        
        if dziennik:
            doc.dziennik = dziennik