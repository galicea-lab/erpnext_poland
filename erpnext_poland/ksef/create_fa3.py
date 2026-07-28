# https://gemini.google.com/app/18b315f613e6ba7f
import frappe
from lxml import etree as et

#from erpnext.accounts.doctype.payment_request.test_payment_request import payment_method
from frappe.utils import flt, formatdate, strip_html,now_datetime


def get_company_address():
  """
  Pobiera adres firmy na podstawie flagi is_your_company_address
  """
  # Zapytanie które zasugerowałeś - posortowane według typu adresu
  adresy = frappe.db.sql("""
                         SELECT name
                         FROM tabAddress
                         WHERE is_your_company_address = 1
                         ORDER BY CASE
                                    WHEN address_type = 'Postal' THEN 1
                                    WHEN address_type = 'Billing' THEN 2
                                    ELSE 3
                                    END
                         """, as_dict=True)

  if adresy:
    # Pobierz pierwszy (najlepiej dopasowany) adres
    adres_doc = frappe.get_doc("Address", adresy[0].name)
    return adres_doc
  return None

def get_receiver(invoice):
  recipient=invoice.custom_recipient
  if not recipient:
    return ('',None)
  dane = frappe.db.sql("""select tax_id,customer_primary_address from tabCustomer where name = '%s'
                         """ % recipient, as_dict=True)
  if dane:
    adres_doc = frappe.get_doc("Address", dane[0].customer_primary_address)
    return (dane[0].tax_id,adres_doc)
  else:
    return ('',None)

def get_customer_address(invoice):
  id_adresu_billingowego = invoice.customer_address
  if id_adresu_billingowego:
    adres_doc = frappe.get_doc("Address", id_adresu_billingowego)
    #sformatowany_adres = adres_doc.get_display()
    return adres_doc
  else:
    return None

def add_podmiot3_odbiorca(root, doc):
    """
    Dodaje sekcję Podmiot3 jako Odbiorcę (Rola 8).
    Dane pobierane są opcjonalnie z dokumentu faktury.
    """
    # Sprawdzamy czy mamy zdefiniowanego odbiorcę (np. w polu custom_recipient)

    odbiorca_nazwa = doc.get("custom_recipient")
    if not odbiorca_nazwa:
        return
    (podmiot3_tax_id, podmiot3_addr) = get_receiver(doc)
    if podmiot3_addr:
      podmiot3 = et.SubElement(root, "Podmiot3")
      # 1. Dane Identyfikacyjne
      dane_id = et.SubElement(podmiot3, "DaneIdentyfikacyjne")
      # Podmiot3 musi mieć identyfikator lub znacznik BrakID [cite: 18, 21]
      # brak NIP dla odbiorcy końcowego:
      #
      if not podmiot3_tax_id:
        et.SubElement(dane_id, "BrakID").text = "1"
      else:
        et.SubElement(dane_id, "NIP").text = podmiot3_tax_id

      # Nazwa odbiorcy [cite: 24]
      et.SubElement(dane_id, "Nazwa").text =odbiorca_nazwa

      # 2. Adres Odbiorcy (opcjonalny w schemacie dla Podmiot3)
      if podmiot3_addr:
        addr3 = et.SubElement(podmiot3, "Adres")
        et.SubElement(addr3, "KodKraju").text = "PL"
        clean_addr = strip_html(podmiot3_addr.get_display())
        lines = clean_addr.split('\n')
        et.SubElement(addr3, "AdresL1").text = lines[0][:512] if lines else "Brak"
        if len(lines) > 1:
            et.SubElement(addr3, "AdresL2").text=lines[1][:512] #" ".join(lines[1:])[:512]
      # 3. Definicja Roli (Obowiązkowa dla Podmiot3)
      # Rola 8 = Odbiorca
      et.SubElement(podmiot3, "Rola").text = "8"

def generate_ksef_xml(invoice_name):
    doc = frappe.get_doc("Sales Invoice", invoice_name)
    company = frappe.get_doc("Company", doc.company)
    customer = frappe.get_doc("Customer", doc.customer) if doc.customer else None

    NS_MAP = {
        None: "http://crd.gov.pl/wzor/2025/06/25/13775/",
        "xsd": "http://www.w3.org/2001/XMLSchema",
        "xsi": "http://www.w3.org/2001/XMLSchema-instance",
        "etd": "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/01/05/eD/DefinicjeTypy/"
    }

    root = et.Element("Faktura", nsmap=NS_MAP)

    # 1. Nagłówek
    naglowek = et.SubElement(root, "Naglowek")
    et.SubElement(naglowek, "KodFormularza", kodSystemowy="FA (3)", wersjaSchemy="1-0E").text = "FA"
    et.SubElement(naglowek, "WariantFormularza").text = "3"
    et.SubElement(naglowek, "DataWytworzeniaFa").text = now_datetime().strftime("%Y-%m-%dT%H:%M:%SZ")

    # 2. Podmiot1 (Sprzedawca)
    podmiot1 = et.SubElement(root, "Podmiot1")
    dane_id1 = et.SubElement(podmiot1, "DaneIdentyfikacyjne")
    et.SubElement(dane_id1, "NIP").text = company.tax_id.strip().replace("-", "")
    et.SubElement(dane_id1, "Nazwa").text = company.custom_company_full_name

    company_address = get_company_address()
    addr1 = et.SubElement(podmiot1, "Adres")
    et.SubElement(addr1, "KodKraju").text = "PL"
    et.SubElement(addr1, "AdresL1").text = f"{company_address.address_line1 or ''} {company_address.address_line2 or ''}".strip()[:512]
    et.SubElement(addr1, "AdresL2").text = f"{company_address.pincode or ''} {company_address.city or ''}".strip()[:512]

    # 3. Podmiot2 (Nabywca)
    podmiot2 = et.SubElement(root, "Podmiot2")
    dane_id2 = et.SubElement(podmiot2, "DaneIdentyfikacyjne")
    if doc.tax_id:
        et.SubElement(dane_id2, "NIP").text = doc.tax_id.strip().replace("-", "")
    else:
        et.SubElement(dane_id2, "BrakID").text = "1" # Zmienione z BrakNIP na BrakID zgodnie ze schematem
    et.SubElement(dane_id2, "Nazwa").text = doc.customer_name

    addr2 = et.SubElement(podmiot2, "Adres")
    et.SubElement(addr2, "KodKraju").text = "PL"
    raw_address = strip_html(doc.address_display or "")
    lines = raw_address.split('\n')
    et.SubElement(addr2, "AdresL1").text = lines[0][:512] if len(lines) > 0 else "Brak"
    if len(lines) > 1:
        et.SubElement(addr2, "AdresL2").text = lines[1][:512]
    if customer and customer.custom_jst>0:
      et.SubElement(podmiot2, "JST").text = "1"
    else:
      et.SubElement(podmiot2, "JST").text = "2"  # nie dotyczy JST ("1", gdy dotyczy)
    et.SubElement(podmiot2, "GV").text = "2"  # nie dotyczy GV
    # Wartość "2" oznacza, że faktura nie dotyczy członka grupy VAT
    # wartość opcjonalna - można pominąć

    # --- Podmiot3 (Odbiorca) ---
    # Musi wystąpić po Podmiot2, a przed sekcją Fa
    add_podmiot3_odbiorca(root, doc)

    # 4. Dane merytoryczne (Fa)
    fa = et.SubElement(root, "Fa")
    et.SubElement(fa, "KodWaluty").text = doc.currency
    et.SubElement(fa, "P_1").text = str(doc.posting_date)
    et.SubElement(fa, "P_2").text = doc.name
    et.SubElement(fa, "P_6").text = str(doc.posting_date)

    # Sumy i adnotacje (bez zmian)
    et.SubElement(fa, "P_13_1").text = f"{flt(doc.net_total):.2f}"
    et.SubElement(fa, "P_14_1").text = f"{flt(doc.total_taxes_and_charges):.2f}"
    et.SubElement(fa, "P_15").text = f"{flt(doc.grand_total):.2f}"

    adnotacje = et.SubElement(fa, "Adnotacje")
    et.SubElement(adnotacje, "P_16").text = "2"
    et.SubElement(adnotacje, "P_17").text = "2"
    et.SubElement(adnotacje, "P_18").text = "2"
    et.SubElement(adnotacje, "P_18A").text = "2"

    zwolnienie = et.SubElement(adnotacje, "Zwolnienie")
    et.SubElement(zwolnienie, "P_19N").text = "1"

    NoweSrodkiTransportu = et.SubElement(adnotacje, "NoweSrodkiTransportu")
    et.SubElement(NoweSrodkiTransportu, "P_22N").text = "1"

    et.SubElement(adnotacje, "P_23").text = "2"

    pmarzy = et.SubElement(adnotacje, "PMarzy")
    et.SubElement(pmarzy, "P_PMarzyN").text = "1"

    et.SubElement(fa, "RodzajFaktury").text = "VAT"

    # Linie faktury
    for i, item in enumerate(doc.items, 1):
        wiersz = et.SubElement(fa, "FaWiersz")
        et.SubElement(wiersz, "NrWierszaFa").text = str(i)
        et.SubElement(wiersz, "P_7").text = item.item_name[:512]
        et.SubElement(wiersz, "P_8A").text = (item.uom or "szt")[:256]
        et.SubElement(wiersz, "P_8B").text = f"{flt(item.qty):.3f}"
        et.SubElement(wiersz, "P_9A").text = f"{flt(item.rate):.2f}"
        et.SubElement(wiersz, "P_11").text = f"{flt(item.net_amount):.2f}"
        et.SubElement(wiersz, "P_12").text = "23"
    payments=doc.get('payment_schedule')
    if payments:
      try:
        payment=payments[0]
        due_date=payment.due_date # creation+credit_days
        if payment.mode_of_payment=='Wire Transfer':
          tryb_platnosci='6'# przelew
        else:
          tryb_platnosci = '6'  # inne na razie nie obsługiwane
        company = frappe.get_doc("Company", doc.company)

        bank_accounts = frappe.get_all(
          "Bank Account",
          filters={"account": company.default_bank_account},
          fields=["name", "bank_account_no", "iban"],
          limit=1
        )

        if bank_accounts:
          iban = bank_accounts[0].get("iban") or bank_accounts[0].get("bank_account_no")

      except:
        pass
      if (due_date and iban and tryb_platnosci):
        platnosc = et.SubElement(fa, "Platnosc")
        termin = et.SubElement(platnosc, "TerminPlatnosci")
        et.SubElement(termin, "Termin").text = due_date.isoformat()
        et.SubElement(platnosc, 'FormaPlatnosci').text=tryb_platnosci
        termin = et.SubElement(platnosc, "RachunekBankowy")
        et.SubElement(termin, "NrRB").text = iban

    # Płatność
    """<Platnosc>
    <TerminPlatnosci>
        <Termin>2026-07-16</Termin>
    </TerminPlatnosci>
    <FormaPlatnosci>6</FormaPlatnosci>
    <RachunekBankowy>
        <NrRB>PL12345678901234567890123456</NrRB>
    </RachunekBankowy>
</Platnosc>"""

    return et.tostring(root, encoding='UTF-8', xml_declaration=True, pretty_print=True)
