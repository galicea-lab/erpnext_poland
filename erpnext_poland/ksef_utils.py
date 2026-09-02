import re
import unicodedata

import frappe
from lxml import etree  as ET

from erpnext_poland.ksef.config import (
    get_accounting_settings,
    ITEMS_MODE_PENDING,
    ITEMS_MODE_PREVIOUS,
    ITEMS_MODE_XML
)
from frappe.utils.file_manager import save_file
from frappe.utils import getdate, nowdate


def compute_vat_month(date_value=None):
  """Miesiąc rozliczenia VAT w formacie RRRRMM (np. 202601)."""
  return getdate(date_value or nowdate()).strftime("%Y%m")


def compute_month(date_value=None):
  """Miesiąc faktury w formacie MM (np. 01)."""
  return getdate(date_value or nowdate()).strftime("%m")


def attach_ksef_xml_to_invoice(invoice_name, xml_content, ksef_number):
  file_name = f"KSeF_{ksef_number}.xml"
  # Używamy save_file zamiast frappe.get_doc("File", ...)
  file_doc = save_file(
    fname=file_name,
    content=xml_content,  # Może być string lub bytes
    dt="Purchase Invoice",
    dn=invoice_name,  # To musi być NAME faktury (np. PINV-2026-0001)
    folder="Home/Attachments",  # Opcjonalne
    is_private=1,
    decode=False
  )
  return file_doc

def import_ksef_header(xml_content, metadata):
    # 1. Tworzenie faktury (Draft)
    doc = frappe.get_doc({
        "doctype": "Purchase Invoice",
        "supplier": metadata['supplier'],
        "bill_no": metadata['ksef_number'],
        "posting_date": metadata['date'],
        "custom_vat_month": compute_vat_month(metadata.get('date')), # RRRRMM
        "custom_ksef_xml": xml_content, # Przechowujemy XML do późniejszego użycia
        "items": [{
            "item_code": "KSeF-PENDING", # Specjalny przedmiot techniczny
            "qty": 1,
            "rate": metadata['total_amount'],
            "description": "Faktura oczekująca na kategoryzację"
        }]
    })
    doc.insert()
    # 2. Załączanie pliku XML do dokumentu
    file_doc = save_file(
        fname=f"KSeF_{metadata['ksef_number']}.xml",
        content=xml_content,
        dt="Purchase Invoice",
        dn=doc.name,
        is_private=1
    )
    # Faktura automatycznie wejdzie w stan 'New' zgodnie z Workflow

@frappe.whitelist()
def send_to_ksef(invoice_name):
    settings = get_accounting_settings()
    # Pobierz dane faktury
    invoice = frappe.get_doc("Sales Invoice", invoice_name)
    from .ksef.create_fa3 import generate_ksef_xml
    xml_str = generate_ksef_xml(invoice_name)
    from .ksef.ksef2int import ksef2_send_invoice

    (referenceNumber,sessionId)=ksef2_send_invoice(xml_str,settings.ksef2.nip,settings.ksef2.cert_pfx,settings.ksef2.cert_pass)
    if sessionId:
        invoice.db_set("ksef_session_id", sessionId)  # zapisz numer KSeF
    if referenceNumber:
        invoice.db_set("ksef_reference_nr", referenceNumber)  # zapisz numer KSeF
        invoice.db_set("ksef_status", "Wysłano")  # custom field
        frappe.msgprint("Faktura wysłana do KSeF: " + referenceNumber)
        frappe.db.commit()
    else:
        frappe.throw("Błąd wysyłki")


def parse_ksef_xml_bak(xml_content):
  root = ET.fromstring(xml_content)

  # Definicja przestrzeni nazw (dla schematu FA(3))
  ns = {
    'ns': 'http://crd.gov.pl/wzor/2025/06/25/13775/',  # Przestrzeń główna
    'ter': 'http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/'
  }


  # Funkcja pomocnicza do pobierania tekstu z uwzględnieniem namespace
  def get_val(path):
    node = root.find(path, ns)
    return node.text if node is not None else None

  # Mapowanie nagłówka faktury
  ksef_data = {
    "ksef_number": get_val(".//ns:NumerKSeF"),  # Jeśli jest w pliku
    "bill_no": get_val(".//ns:Fa/ns:P_2"),  # Numer faktury sprzedawcy
    "posting_date": get_val(".//ns:Fa/ns:P_1"),  # Data wystawienia
    "currency": get_val(".//ns:Fa/ns:KodWaluty"),
    "total_amount": float(get_val(".//ns:Fa/ns:P_15") or 0),
    "supplier_nip": get_val(".//ns:Podmiot1/ns:DaneIdentyfikacyjne/ns:NIP"),
    "supplier": get_val(".//ns:Podmiot1/ns:DaneIdentyfikacyjne/ns:Nazwa"),
    "items": []
  }

  # Pobieranie pozycji (tylko jeśli chcesz je od razu, np. do sumowania)
  for wiersz in root.findall(".//ns:Fa/ns:FaWiersz", ns):
    try:
      vat_rate=wiersz.find("ns:P_12", ns).text  # np. "23"
    except:
      vat_rate='23'
    ksef_data["items"].append({
      "description": wiersz.find("ns:P_7", ns).text if wiersz.find("ns:P_7",
                                                                   ns) is not None else "Brak opisu",
      "qty": float(wiersz.find("ns:P_8B", ns).text or 1) if wiersz.find("ns:P_8B",
                                                                        ns) is not None else 1,
      "net_rate": float(wiersz.find("ns:P_9A", ns).text or 0),
      "vat_rate":vat_rate
    })
  return ksef_data


import xml.etree.ElementTree as ET


def parse_ksef_xml(xml_content):
  root = ET.fromstring(xml_content)

  # Definicja przestrzeni nazw (schemat FA(3))
  ns = {
    'ns': 'http://crd.gov.pl/wzor/2025/06/25/13775/',
    'ter': 'http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/'
  }

  # Bezpieczna funkcja pomocnicza: pobiera tekst z dowolnego elementu nadrzędnego
  def get_val(element, path, default=None):
    node = element.find(path, ns)
    if node is not None and node.text is not None:
      return node.text
    return default

  # Mapowanie nagłówka faktury (szukamy względem root)
  ksef_data = {
    "ksef_number": get_val(root, ".//ns:NumerKSeF"),
    "bill_no": get_val(root, ".//ns:Fa/ns:P_2"),
    "posting_date": get_val(root, ".//ns:Fa/ns:P_1"),
    "currency": get_val(root, ".//ns:Fa/ns:KodWaluty", "PLN"),  # Domyślnie PLN
    "total_amount": float(get_val(root, ".//ns:Fa/ns:P_15", 0)),
    "supplier_nip": get_val(root, ".//ns:Podmiot1/ns:DaneIdentyfikacyjne/ns:NIP"),
    "supplier": get_val(root, ".//ns:Podmiot1/ns:DaneIdentyfikacyjne/ns:Nazwa"),
    "items": []
  }

  # Pobieranie pozycji faktury
  for wiersz in root.findall(".//ns:Fa/ns:FaWiersz", ns):
    # W KSeF cena jednostkowa może być w P_9A (netto) lub P_9B (np. brutto/marża)
    net_rate_str = get_val(wiersz, "ns:P_9A")
    if net_rate_str is None:
      # Jeśli nie ma P_9A (netto), awaryjnie pobieramy P_9B
      net_rate_str = get_val(wiersz, "ns:P_9B", 0)

    ksef_data["items"].append({
      "description": get_val(wiersz, "ns:P_7", "Brak opisu"),
      "qty": float(get_val(wiersz, "ns:P_8B", 1)),
      "net_rate": float(net_rate_str),
      "vat_rate": get_val(wiersz, "ns:P_12", "23")  # Pobiera VAT, brak rzuci domyślne '23'
    })

  return ksef_data

def _slugify_item_code(description):
  """Buduje kod asortymentu (ASCII, A-Z0-9 i myślniki) z opisu pozycji KSeF."""
  text = unicodedata.normalize("NFKD", description or "")
  text = text.encode("ascii", "ignore").decode("ascii")
  code = re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-").upper()
  return code[:140] or "KSEF-ITEM"


def get_or_create_item_from_description(description):
  """Zwraca item_code dla podanego opisu z formularza KSeF,
  tworząc definicję Item jeśli jeszcze nie istnieje."""
  desc = (description or "").strip() or "Brak opisu"
  existing = frappe.get_all(
      "Item",
      filters={"item_name": desc},
      fields=["name"],
      order_by="creation asc",
      limit_page_length=1
  )
  if existing:
    return existing[0].name

  item_code = _slugify_item_code(desc)
  if frappe.db.exists("Item", item_code):
    # Kod zajęty przez inny asortyment – dopisujemy licznik
    i = 2
    while frappe.db.exists("Item", f"{item_code}-{i}"):
      i += 1
    item_code = f"{item_code}-{i}"

  item_group = frappe.db.get_single_value("Stock Settings", "default_item_group") \
      or frappe.db.get_value("Item Group", {}, "name")
  if not item_group:
    frappe.throw("Nie można utworzyć asortymentu: brak grupy asortymentowej (Item Group). "
                 "Utwórz grupę lub ustaw domyślną w Ustawieniach magazynowych.")

  new_item = frappe.get_doc({
    "doctype": "Item",
    "item_code": item_code,
    "item_name": desc,
    "item_group": item_group,
    "stock_uom": "Unit",
    "is_stock_item": 0,
    "is_fixed_asset": 0,
    "is_purchase_item": 1,
    "is_sales_item": 0
  })
  new_item.insert()
  frappe.msgprint(f"Utworzono nowy asortyment: <b>{item_code}</b> ({desc})")
  return new_item.name


def get_items_from_previous_invoice(supplier, settings):
  """Pozycje z ostatniej faktury zakupu tego dostawcy
  (bez technicznej pozycji KSeF-PENDING)."""
  prev = frappe.get_all(
      "Purchase Invoice",
      filters={
        "supplier": supplier,
        "docstatus": ["!=", 2]
      },
      fields=["name"],
      order_by="posting_date desc, creation desc",
      limit_page_length=1
  )
  if not prev:
    return []
  rows = frappe.get_all(
      "Purchase Invoice Item",
      filters={"parenttype": "Purchase Invoice", "parent": prev[0].name},
      fields=["item_code", "qty", "uom", "rate", "description", "expense_account"],
      order_by="idx asc"
  )
  pending_codes = {settings.ksef2.item_code, "KSeF-PENDING"}
  items = []
  for r in rows:
    if r.item_code in pending_codes:
      continue
    row = {
      "item_code": r.item_code,
      "qty": r.qty,
      "uom": r.uom,
      "rate": r.rate,
      "description": r.description
    }
    if r.expense_account:
      row["expense_account"] = r.expense_account
    items.append(row)
  return items


def build_invoice_items(mode, ksef_data, supplier, settings):
  """Buduje listę pozycji faktury zakupu zgodnie z wybranym trybem:
  - ITEMS_MODE_PENDING  : jedna techniczna pozycja KSeF-PENDING (dotychczasowe zachowanie)
  - ITEMS_MODE_PREVIOUS : kopie pozycji z ostatniej faktury tego dostawcy
  - ITEMS_MODE_XML      : pozycje odczytane z formularza KSeF (tworzy brakujące definicje)
  W razie braku danych wraca do trybu KSeF-PENDING."""
  if mode == ITEMS_MODE_PREVIOUS:
    items = get_items_from_previous_invoice(supplier, settings)
    if items:
      return items
    frappe.msgprint(
        msg=f"Brak wcześniejszych pozycji dla dostawcy <b>{supplier}</b>. "
            "Użyto pozycji technicznej.",
        title="KSeF",
        indicator="orange"
    )
  elif mode == ITEMS_MODE_XML:
    xml_items = []
    for row in ksef_data.get('items') or []:
      desc = row.get('description') or "Brak opisu"
      xml_items.append({
        "item_code": get_or_create_item_from_description(desc),
        "qty": row.get('qty') or 1,
        "rate": row.get('net_rate') or 0,
        "description": desc,
        "uom": "Unit"
      })
    if xml_items:
      return xml_items
    frappe.msgprint(
        msg="Formularz KSeF nie zawiera pozycji. Użyto pozycji technicznej.",
        title="KSeF",
        indicator="orange"
    )

  # Faktury proste (1-2 pozycje): zamiast pozycji technicznej używamy
  # danych z pierwszej pozycji formularza KSeF (kartoteka Item zakładana automatycznie)
  xml_items = ksef_data.get('items') or []
  if len(xml_items) in (1, 2):
    first = xml_items[0]
    desc = first.get('description') or "Brak opisu"
    return [{
      "item_code": get_or_create_item_from_description(desc),
      "qty": first.get('qty') or 1,
      "rate": first.get('net_rate') or 0,
      "description": desc,
      "uom": "Unit"
    }]

  # Tryb domyślny: pozycja techniczna na łączną kwotę
  return [{
    "item_code": settings.ksef2.item_code,
    "qty": 1,
    "rate": ksef_data['total_amount'],
    "description": settings.ksef2.description
  }]


def map_item(item):
  return 'Pieczęć elektroniczna'

@frappe.whitelist()
def register_from_ksef():
  from .ksef.ksef2int import ksef2_receive_invoices #ksef2_receive_invoices_test
  from .utils.dbint import get_or_create_supplier_by_nip
  settings = get_accounting_settings()

  #for ksefID in ksef2_receive_invoices_test():
  for ksefID in ksef2_receive_invoices():
    try:
      print(ksefID)
      if not ksefID:
        # KSeF nie zwrócił jeszcze numeru dla tej faktury (opóźnienie po stronie KSeF) -
        # pomijamy, kolejne uruchomienie crona (zakres 30 dni) spróbuje ponownie.
        frappe.log_error(
            "Otrzymano fakturę z KSeF bez przydzielonego numeru KSeF (ksefNumber) - "
            "import pominięty, zostanie ponowiony przy kolejnym uruchomieniu.",
            "KSeF - brak numeru faktury"
        )
        continue
      purchase_invoice = frappe.get_all("Purchase Invoice",
                                           filters={
                                             "ksef_numer":ksefID
                                           },
                                          fields=['name', 'ksef_numer']
                                           )
      if not  purchase_invoice:
        file_name=f"{ksefID}.xml"
        with open(file_name,'rb') as f:
          xml_string=f.read()
        ksef_data=parse_ksef_xml(xml_string)
        supplier=get_or_create_supplier_by_nip(ksef_data['supplier_nip'], ksef_data['supplier'])
        new_invoice = frappe.get_doc({
          "doctype": "Purchase Invoice",
          "supplier": supplier,
          "posting_date": ksef_data['posting_date'],
          "bill_no": ksef_data['bill_no'],
          "currency": ksef_data['currency'],
          "total_amount": ksef_data['total_amount'],
          "ksef_numer": ksefID,
          "custom_vat_month": compute_vat_month(ksef_data['posting_date']), # RRRRMM
          "custom_month": compute_month(ksef_data['posting_date']), # MM
          "items": build_invoice_items(settings.ksef2.items_mode, ksef_data, supplier, settings)
        })
        if  ksef_data['currency']=='USD':  # !!! hardcoded - do poprawy
          new_invoice.credit_to = settings.ksef2.credit_to_usd #'210.01.2 - Rozrachunki z dostawcami krajowymi - USD - TM', #!!!!
          for row in new_invoice.items:
            if not row.get("expense_account"):
              row.expense_account = settings.ksef2.default_expense_account
        # Dodawanie pozycji faktury
        new_invoice.insert()
        # Teraz dołączamy plik, używając 'name' nowo utworzonej faktury
        file_doc=attach_ksef_xml_to_invoice(new_invoice.name, xml_string, ksefID)
        frappe.db.commit()
        new_invoice.add_comment(
            "Attachment",
            f"Odebrano i dołączono fakturę zakupu: <a href='{file_doc.file_url}'>{file_doc.file_name}</a>"
        )
        # Można odświeżyć pole _attachments (czasami pomaga w UI)
        new_invoice.set("__attachments", True)
        frappe.msgprint(
            msg = f"Plik został dołączony jako załącznik.<br><b>{file_doc.file_name}</b>",
            title = "Sukces",
            indicator = "green"
        )

        """
        return {
            "status": "success",
            "file_url": file_doc.file_url,
            "file_name": file_doc.file_name
        }
        """
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Błąd pobierania KSeF")
        frappe.throw(f"Nie udało się wygenerować / zapisać pliku faktury: {str(e)}")
  return {
          "status": "OK",
    }


@frappe.whitelist()
def check_sent_invoices_status():
  """Funkcja do uruchamiania przez Cron (Scheduled Job)"""
  #from .ksef.config import settings
  #from .ksef.ksef2client.client import KSeFClient
  from .ksef.ksef2int import ksef2_get_nr

  # Pobierz faktury, które zostały wysłane, ale nie mają jeszcze numeru KSeF
  pending_invoices = frappe.get_all("Sales Invoice",
                                    filters={
                                      "ksef_status": "Wysłano",
                                      "ksef_session_id": ["!=", None]
                                    },
                                    fields=["name", "ksef_reference_nr", "ksef_session_id"])

  if not pending_invoices:
    return
  token=None
  for inv in pending_invoices:
    if inv.ksef_session_id:
      try:
        # Pobieramy faktury z sesji (korzystając z ksef_reference_nr zapisanego przy wysyłce)
        # W modelu KSeF, status faktury sprawdza się w kontekście sesji
        (resp_invoices,token)=ksef2_get_nr(token, inv.ksef_session_id)
        for ksef_inv in resp_invoices.invoices:
          if ksef_inv.status.code == 200:
            # Sprawdzamy status konkretnej faktury (kod 200 oznacza sukces)
            if ksef_inv.ksefNumber:
              doc = frappe.get_doc("Sales Invoice", inv.name)
              doc.db_set("ksef_numer", ksef_inv.ksefNumber)
              doc.db_set("ksef_status", "Przyjęto")
              doc.db_set("ksef_data_wystawienia", ksef_inv.acquisitionDate) # invoicingDate
              doc.add_comment("Info",
                            f"Faktura zaakceptowana przez KSeF. Numer: {ksef_inv.ksefNumber}")
              frappe.db.commit()
          elif ksef_inv.status.code >= 400:
              frappe.get_doc("Sales Invoice", inv.name).db_set("ksef_status", "Błąd")
              frappe.log_error(f"Błąd KSeF dla {inv.name}: {ksef_inv.status.description}",
                               "KSeF Status Error")

      except Exception as e:
        frappe.log_error(f"Problem przy sprawdzaniu statusu {inv.name}: {str(e)}",
                         "KSeF Status Sync")
