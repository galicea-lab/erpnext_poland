import frappe
from frappe import _

def get_or_create_supplier_by_nip(nip, supplier_name=None, defaults=None):
    """
    Sprawdza czy istnieje dostawca o podanym NIP (tax_id).
    Jeśli tak → zwraca jego supplier_name
    Jeśli nie → tworzy nowego i zwraca nowo nadaną nazwę

    Parametry:
        nip (str): numer NIP / VAT (pole tax_id)
        supplier_name (str, optional): proponowana nazwa dostawcy (jeśli nie podano → używa NIP jako nazwę)
        defaults (dict, optional): dodatkowe pola przy tworzeniu, np.
            {
                "supplier_group": "Dostawcy krajowi",
                "supplier_type": "Company",
                "country": "Poland",
                "tax_category": "Zakup krajowy",
                ...
            }

    Zwraca:
        str: supplier_name (istniejącego lub nowo utworzonego dostawcy)
    """
    if not nip:
        frappe.throw(_("NIP jest wymagany"))

    nip = nip.strip().replace("-", "").replace(" ", "")

    # Szukamy po tax_id
    supplier = frappe.db.get_value(
        "Supplier",
        filters={"tax_id": nip},
        fieldname=["name", "supplier_name"],
        as_dict=True
    )

    if supplier:
        return supplier.supplier_name

    # Nie znaleziono → tworzymy nowego
    if not supplier_name:
        supplier_name = f"Dostawca {nip}"

    if not defaults:
        defaults = {}

    # Domyślne sensowne wartości (dostosuj do swojego systemu!)
    #defaults.setdefault("supplier_group", "Dystrybutor") #"Dostawcy")          # musisz mieć taką grupę
    defaults.setdefault("supplier_type", "Company")
    defaults.setdefault("country", "Poland")
    # defaults.setdefault("tax_category", "Zakup krajowy")     # jeśli używasz

    new_supplier = frappe.get_doc({
        "doctype": "Supplier",
        "supplier_name": supplier_name,
        "tax_id": nip,
        **defaults
    })

    try:
        new_supplier.insert(ignore_permissions=False)  # zmień na True jeśli chcesz ominąć permisje
        frappe.msgprint(_("Utworzono nowego dostawcę: {0} ({1})").format(
            new_supplier.supplier_name, new_supplier.name
        ))
        return new_supplier.supplier_name

    except frappe.DuplicateEntryError:
        # race condition – ktoś utworzył w międzyczasie
        frappe.clear_messages()
        # ponawiamy odczyt
        supplier_name = frappe.db.get_value(
            "Supplier", {"tax_id": nip}, "supplier_name"
        )
        if supplier_name:
            return supplier_name
        else:
            frappe.throw(_("Błąd podczas tworzenia dostawcy – duplikat, ale nie można odczytać"))

    except Exception as e:
        frappe.throw(_("Błąd podczas tworzenia dostawcy: {0}").format(str(e)))


def test():
  # -------------------------------
  # Przykłady użycia
  # -------------------------------

  # 1. Najprostsze wywołanie (nazwa = NIP)
  nazwa = get_or_create_supplier_by_nip("7740001454")
  print(nazwa)   # → "Dostawca 7740001454" lub istniejąca nazwa

  # 2. Z własną nazwą
  nazwa = get_or_create_supplier_by_nip(
      "5251001282",
      supplier_name="ABC Serwis Sp. z o.o."
  )

  # 3. Z dodatkowymi polami
  nazwa = get_or_create_supplier_by_nip(
      "6312650479",
      supplier_name="Nowy Hurtownia",
      defaults={
          "supplier_group": "Dostawcy krajowi",
          "supplier_type": "Company",
          "country": "Poland",
          "default_price_list": "Standard Buying",
          "payment_terms": "30 dni"
      }
  )
