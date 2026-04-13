# jpk_v7m_generator.py
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, Dict, List, Tuple, Any
import frappe
from frappe import _
from pydantic import ValidationError
import json
from dateutil import parser

import xml.etree.ElementTree as ET
from xml.dom import minidom

def get_decimal(w, attr):
  """Bezpieczne pobranie wartości Decimal, zawsze zwraca Decimal"""
  val = getattr(w, attr, None)
  if val is None:
    return Decimal('0')
  return Decimal(str(val))  # konwersja na wypadek gdyby to był float/int

TINs = {
  'Poland':'PL',
  'United States':'USA'
}

# Import modeli Pydantic
from .models_jpk_v7m import (
  Naglowek, Podmiot1, Deklaracja, DeklaracjaNaglowek,
  PozycjeSzczegolowe,
  SprzedazWiersz, ZakupWiersz, Ewidencja, Jpk,
  OsobaFizyczna, OsobaNiefizyczna
)

def get_customer_address(invoice):
  if invoice.customer_address:
    return frappe.get_doc("Address", invoice.customer_address)
  else:
    return None


class JPK_V7M_Generator:
  def __init__(self, company: str, year: int, month: int,
         cel_zlozenia: str = "1", kod_urzedu: str = None,
         przeniesienie : Decimal=0):
    """
    Inicjalizacja generatora JPK-V7M

    Args:
      company: Nazwa firmy w ERPNext
      year: Rok rozliczeniowy (>= 2026)
      month: Miesiąc rozliczeniowy (1-12)
      cel_zlozenia: Cel złożenia ("1" - pierwsze, "2" - korekta)
      kod_urzedu: Kod urzędu skarbowego
      przeniesienie: z poprzedniego miesiąca
    """
    self.imp_vat_rate=Decimal(23) # tymczasowo - nie wiem jak to ma być JW
    self.company = company
    self.year = year
    self.month = month
    self.cel_zlozenia = cel_zlozenia
    self.kod_urzedu = kod_urzedu or self._get_default_kod_urzedu()
    self.przeniesienie=przeniesienie

    # Pobierz dane firmy
    self.company_data = self._get_company_data()
    self.company_address = self._get_company_address()

    # Słowniki mapowań
    self.gtu_mapping = {
      "": "",
      "GTU_01": "GTU_01",
      "GTU_02": "GTU_02",
      "GTU_03": "GTU_03",
      "GTU_04": "GTU_04",
      "GTU_05": "GTU_05",
      "GTU_06": "GTU_06",
      "GTU_07": "GTU_07",
      "GTU_08": "GTU_08",
      "GTU_09": "GTU_09",
      "GTU_10": "GTU_10",
      "GTU_11": "GTU_11",
      "GTU_12": "GTU_12",
      "GTU_13": "GTU_13"
    }

    self.procedure_mapping = {
      "EE": "WSTO_EE",
      "SW": "IED",
      "TP": "TP",
      "TT_WNT": "TT_WNT",
      "TT_D": "TT_D",
      "MR_T": "MR_T",
      "MR_UZ": "MR_UZ",
      "I_42": "I_42",
      "I_63": "I_63",
      "B_SPV": "B_SPV",
      "B_SPV_DOSTAWA": "B_SPV_DOSTAWA",
      "B_MPV_PROWIZJA": "B_MPV_PROWIZJA"
    }

    self.typ_transakcji_mapping = {
      "SP": "",  # Sprzedaż
      "WEW": "WEW",  # Wewnętrzny
      "ZAK": "MK",  # Zakup
      "IMP": "MK",  # Import
      "EKS": "",  # Eksport
      "SW": "WEW",  # Świadczenie wewnętrzne
      "INNE": ""  # Inne
    }

  def _get_default_kod_urzedu(self) -> str:
    """Pobierz domyślny kod urzędu skarbowego na podstawie adresu firmy"""
    # Tutaj można zaimplementować logikę mapowania kodu urzędu
    # Na razie zwracamy przykładowy kod
    return "1804"

  def _get_company_data(self) -> Dict:
    """Pobierz dane firmy z ERPNext"""
    company = frappe.get_doc("Company", self.company)
    try:
      phone=company.phone_no
    except:
      phone=''
    return {
      "name": company.name,
      "tax_id": company.tax_id,
      "company_name": company.custom_company_full_name,
      "email": company.email,
      "phone": phone
    }

  def _get_company_address(self) -> Dict:
    """Pobierz adres firmy"""
    address = frappe.get_all("Dynamic Link",
                 filters={
                   "link_doctype": "Company",
                   "link_name": self.company,
                   "parenttype": "Address"
                 },
                 fields=["parent"],
                 limit=1
                 )

    if address:
      address_doc = frappe.get_doc("Address", address[0].parent)
      return {
        "address_line1": address_doc.address_line1,
        "city": address_doc.city,
        "county": address_doc.county,
        "state": address_doc.state,
        "country": address_doc.country,
        "pincode": address_doc.pincode
      }
    return {}

  def _get_podmiot(self) -> Podmiot1:
    """Utwórz sekcję Podmiot1 na podstawie danych firmy"""
    # Sprawdź czy firma ma NIP (osoba niefizyczna) czy PESEL (osoba fizyczna)
    if self.company_data.get("pesel"): # !! do zrobienia - na razie tylko nifizyczne
      # Osoba fizyczna (domyślnie - należy dostosować do rzeczywistych danych)
      osoba_fizyczna = OsobaFizyczna(
        nip=self.company_data.get("tax_id", "").strip(),
        imie_pierwsze="",  # Należy pobrać z odpowiedniego pola
        nazwisko=self.company_data["company_name"],
        data_urodzenia=date(1970, 1, 1),  # Należy pobrać z odpowiedniego pola
        pesel=self.company_data.get("pesel"),
        email=self.company_data.get("email", ""),
        telefon=self.company_data.get("phone")
      )
      return Podmiot1(osoba_fizyczna=osoba_fizyczna)
    else:
      # Osoba niefizyczna (firma)
      osoba_niefizyczna = OsobaNiefizyczna(
        nip=self.company_data["tax_id"].strip(),
        pelna_nazwa=self.company_data["company_name"],
        email=self.company_data.get("email", ""),
        telefon=self.company_data.get("phone")
      )
      return Podmiot1(osoba_niefizyczna=osoba_niefizyczna)

  def _get_sprzedaz_data(self) -> Tuple[List[SprzedazWiersz], Decimal]:
    """Pobierz dane sprzedaży dla danego okresu"""

    """
      "posting_date": ["between",
               [f"{self.year}-{self.month:02d}-01",
                f"{self.year}-{self.month:02d}-31"]],
    """
    sales_invoices = frappe.get_all("Sales Invoice",
                    filters={
                      "company": self.company,
                      "custom_vat_month": f"{self.year}{self.month:02d}",
                      "docstatus": 1  # Tylko zatwierdzone faktury
                    },
                    fields=["name", "posting_date", "ksef_data_sprzedazy", "customer",
                        "customer_name",
                        "tax_id", "base_total","base_net_total",
                        "base_total_taxes_and_charges",
                        "ksef_data_sprzedazy", "ksef_data_wystawienia",
                        "jpk_vat_typ_transakcji", "jpk_vat_gtu",
                        "jpk_vat_ied", "jpk_vat_ied_kraj",
                        "jpk_procedura_vat", "ksef_numer"]
                    )
    sprzedaz_wiersze = []
    total_sprzedaz = Decimal('0')

    for idx, invoice in enumerate(sales_invoices, 1):
      # Pobierz stawkę VAT i podatek
      vat_rate, vat_amount = self._get_invoice_vat_details(invoice["name"])

      # Określ typ dokumentu
      typ_dokumentu = self._determine_invoice_type(invoice)

      # Określ pola K_* na podstawie typu transakcji i stawki VAT
      k_fields = self._calculate_k_fields(invoice, vat_rate, vat_amount)

      # Dodaj GTU jeśli jest ustawione
      gtu_fields = self._get_gtu_fields(invoice.get("jpk_vat_gtu"))

      # Dodaj pola procedur jeśli są ustawione
      procedure_fields = self._get_procedure_fields(invoice.get("jpk_procedura_vat"))

      # Data sprzedaży - preferuj ksef_data_sprzedazy, potem posting_date
      data_sprzedazy = (invoice.get("ksef_data_sprzedazy") or
                invoice.get("posting_date"))
      customer=frappe.get_doc('Customer', invoice.get("customer"))
      #adres=get_customer_address(invoice)
      TIN=''
      czy_podmiot_powiazany=customer.get('czy_podmiot_powiazany')
      tax_id=invoice.get("tax_id") or ""
      if tax_id and tax_id[0].isalpha():
        TIN=tax_id[:2]
        tax_id=tax_id[2:]
      if tax_id=='EU528002224': # !!! poprawic
        tax_id='528002224'
        TIN='USA'

      sprzedaz_wiersz = SprzedazWiersz(
        lp_sprzedazy=idx,
        TIN=TIN,
        nr_kontrahenta=tax_id,
        nazwa_kontrahenta=invoice.get("customer_name") or invoice.get("customer"),
        ksef_numer=invoice.get("ksef_numer") or '',
        dowod_sprzedazy=invoice["name"],
        data_wystawienia=invoice.get("ksef_data_wystawienia") or invoice["posting_date"],
        data_sprzedazy=data_sprzedazy,
        typ_dokumentu=typ_dokumentu,
        **k_fields,
        **gtu_fields,
        podmiot_powiazany=czy_podmiot_powiazany or False,
        **procedure_fields
      )

      sprzedaz_wiersze.append(sprzedaz_wiersz)
      total_sprzedaz += Decimal(str(invoice.get("base_total", 0)))

    return sprzedaz_wiersze, total_sprzedaz

  def _get_zakup_data(self, sprzedaz_wiersze : List[SprzedazWiersz], total_sprzedaz : Decimal) -> tuple[list[Any], Decimal, Decimal]:
    """Pobierz dane zakupów dla danego okresu"""
    """ jeśli import usług - dodaje do sprzedaży """
    purchase_invoices = frappe.get_all("Purchase Invoice",
                       filters={
                         "company": self.company,
                         "custom_vat_month":f"{self.year}{self.month:02d}",
                         "docstatus":("not like", "2")  # Tylko nie anulowane
                       },
                       fields=["name", "posting_date", "ksef_data_sprzedazy", "supplier",
                           "supplier_name",
                           "tax_id", "base_total","base_net_total",
                           "base_total_taxes_and_charges",
                           "bill_no", "bill_date", "jpk_vat_typ_transakcji",
                           "jpk_procedura_vat", "ksef_numer"]
                       )

    zakup_wiersze = []
    total_zakup = Decimal('0')
    for idx, invoice in enumerate(purchase_invoices, 1):
      # Pobierz stawkę VAT i podatek
      vat_rate, vat_amount = self._get_invoice_vat_details(invoice["name"], is_purchase=True)

      # Określ typ dokumentu zakupu
      #dokument_zakupu = self._determine_dokument_zakupu_type(invoice)

      supplier=frappe.get_doc('Supplier', invoice.get("supplier"))
      country=supplier.get('country')
      if country in TINs:
        TIN=TINs[country]
      else:
        TIN=''
      tax_id=invoice.get("tax_id") or ""
      if tax_id and tax_id[0].isalpha():
        tax_id=tax_id[2:]

      # Oblicz pola K_42 i K_43
      k_42, k_43 = self._calculate_zakup_k_fields(invoice, vat_rate, vat_amount)
      zakup_wiersz = ZakupWiersz(
        lp_zakupu=idx,
        TIN=TIN,
        nr_dostawcy=tax_id,
        ksef_numer=invoice.get("ksef_numer") or '',
        nazwa_dostawcy=invoice.get("supplier_name") or invoice.get("supplier"),
        dowod_zakupu=invoice["bill_no"],
        data_zakupu=invoice.get("ksef_data_sprzedazy") or invoice.get("bill_date") or invoice["posting_date"],
        k_42=k_42,
        k_43=k_43
      )
      zakup_wiersze.append(zakup_wiersz)
      total_zakup += Decimal(str(invoice.get("base_total", 0)))
      if invoice.get("jpk_vat_typ_transakcji")=='IMP':
        sidx=1 if not sprzedaz_wiersze else sprzedaz_wiersze[-1].lp_sprzedazy+1
        if invoice.get("ksef_data_sprzedazy"):
          data_sprzedazy=invoice.get("ksef_data_sprzedazy")
        else:
          data_sprzedazy=invoice["posting_date"]
        sprzedaz_wiersz = SprzedazWiersz(
          lp_sprzedazy=sidx,
          nr_kontrahenta=invoice.get("tax_id") or "",
          ksef_numer=invoice.get("ksef_numer") or '',
          nazwa_kontrahenta=invoice.get("supplier_name") or invoice.get("supplier"),
          dowod_sprzedazy=invoice["bill_no"],
          data_wystawienia=invoice["posting_date"] if (not invoice.get("bill_date")) or (
                                                invoice["posting_date"] and
                                                invoice["posting_date"]<=invoice.get("bill_date"))
                                                   else invoice.get("bill_date"),
          data_sprzedazy=data_sprzedazy,
          k_27=k_42,
          k_28=k_43
        )

        sprzedaz_wiersze.append(sprzedaz_wiersz)
        total_sprzedaz += Decimal(str(invoice.get("base_total", 0)))
        #total_imp+=k_42
        #total_imp_vat+=(self.imp_vat_rate*k_42/100)#vat_amount


    return zakup_wiersze, total_zakup, total_sprzedaz #total_imp, total_imp_vat

  def _get_invoice_vat_details(self, invoice_name: str, is_purchase: bool = False) -> Tuple[
    Decimal, Decimal]:
    """Pobierz szczegóły VAT dla faktury"""
    doctype = "Purchase Invoice" if is_purchase else "Sales Invoice"
    invoice = frappe.get_doc(doctype, invoice_name)

    # Pobierz sumę podatku VAT
    vat_amount = Decimal(str(invoice.get("base_total_taxes_and_charges", 0)))

    # Oblicz stawkę VAT (uproszczone - średnia ważona)
    if invoice.get("base_net_total", 0) > 0:
      #  poprawka na sytuacje, gdy nie wprowadzono podatków !!! UWAGA! Jak uwzględnić zerowe?
      if vat_amount==0:
        vat_rate=self.imp_vat_rate
        vat_amount=Decimal(str(invoice.base_net_total))*self.imp_vat_rate/100
      else:
        vat_rate = (vat_amount / Decimal(str(invoice.base_net_total))) * 100
    else:
      vat_rate = Decimal('0')

    return vat_rate, vat_amount

  def _determine_invoice_type(self, invoice: Dict) -> Optional[str]:
    """Określ typ dokumentu sprzedaży"""
    typ_transakcji = invoice.get("jpk_vat_typ_transakcji")

    if typ_transakcji in self.typ_transakcji_mapping:
      return self.typ_transakcji_mapping[typ_transakcji]

    # Domyślnie ''
    return ""

  def _determine_dokument_zakupu_type(self, invoice: Dict) -> Optional[str]:
    """Określ typ dokumentu zakupu"""
    typ_transakcji = invoice.get("jpk_vat_typ_transakcji")

    if typ_transakcji == "IMP":
      return "MK"  # Import
    elif typ_transakcji == "ZAK":
      return "MK"  # Zakup krajowy
    elif typ_transakcji == "WEW":
      return "WEW"  # Wewnętrzny

    return "MK"  # Domyślnie MK

  def _calculate_k_fields(self, invoice: Dict, vat_rate: Decimal, vat_amount: Decimal) -> Dict:
    """Oblicz pola K_* dla sprzedaży na podstawie stawki VAT"""
    base_amount = Decimal(str(invoice.get("base_net_total", 0)))
    k_fields = {}

    # Mapowanie stawki VAT na odpowiednie pola
    vat_rate_str = str(round(vat_rate, 0))

    if vat_rate == 0:
      # Sprawdź typ transakcji dla stawki 0%
      typ_transakcji = invoice.get("jpk_vat_typ_transakcji")
      if typ_transakcji in ["EKS", "SW"]:
        k_fields["k_13"] = base_amount  # Eksport/Świadczenia międzynarodowe
      else:
        k_fields["k_10"] = base_amount  # Zwolnione

    elif vat_rate == 5:
      k_fields["k_15"] = base_amount
      k_fields["k_16"] = vat_amount

    elif vat_rate in [7, 8]:
      k_fields["k_17"] = base_amount
      k_fields["k_18"] = vat_amount

    elif vat_rate in [22, 23]:
      k_fields["k_19"] = base_amount
      k_fields["k_20"] = vat_amount

    # Dodatkowe pola dla specjalnych transakcji
    typ_transakcji = invoice.get("jpk_vat_typ_transakcji")
    if typ_transakcji == "SW":  # Wewnątrzwspólnotowa dostawa
      k_fields["k_21"] = base_amount
    elif typ_transakcji == "EKS":  # Eksport
      k_fields["k_22"] = base_amount

    return k_fields

  def _calculate_zakup_k_fields(self, invoice: Dict, vat_rate: Decimal, vat_amount: Decimal) -> \
  Tuple[Optional[Decimal], Optional[Decimal]]:
    """Oblicz pola K_42 i K_43 dla zakupów"""
    base_amount = Decimal(str(invoice.get("base_net_total", 0)))

    # Sprawdź czy to środek trwały (uproszczone założenie)
    is_fixed_asset = self._check_if_fixed_asset(invoice["name"])

    if is_fixed_asset:
      # K_40 i K_41 dla środków trwałych
      return None, None  # W rzeczywistości zwróć k_40, k_41
    else:
      # K_42 i K_43 dla pozostałych zakupów
      return base_amount, vat_amount

  def _check_if_fixed_asset(self, invoice_name: str) -> bool:
    """Sprawdź czy faktura zawiera środki trwałe"""
    # Sprawdź w pozycjach faktury czy są oznaczone jako środki trwałe
    items = frappe.get_all("Purchase Invoice Item",
                 filters={"parent": invoice_name, "is_fixed_asset": 1},
                 limit=1
                 )
    return len(items) > 0

  def _get_gtu_fields(self, gtu_code: Optional[str]) -> Dict:
    """Mapuj kod GTU na odpowiednie pola"""
    if not gtu_code or gtu_code not in self.gtu_mapping:
      return {}

    return {gtu_code: 1}

  def _get_procedure_fields(self, procedure_code: Optional[str]) -> Dict:
    """Mapuj kod procedury na odpowiednie pola"""
    if not procedure_code or procedure_code not in self.procedure_mapping:
      return {}

    return {self.procedure_mapping[procedure_code]: 1}


  def _calculate_deklaracja(self, ewidencja : Ewidencja) -> Deklaracja:
    """
    Oblicz pozycje szczegółowe deklaracji na podstawie ewidencji
    """
    # ========== PODATEK NALEŻNY ==========
    # Inicjalizacja sum dla poszczególnych stawek
    p_10 = Decimal('0')  # Zwolnione
    p_11 = Decimal('0')  # Poza terytorium kraju
    p_13 = Decimal('0')  # Stawka 0%
    p_15 = Decimal('0')  # Podstawa 5%
    p_16 = Decimal('0')  # Podatek 5%
    p_17 = Decimal('0')  # Podstawa 8%
    p_18 = Decimal('0')  # Podatek 8%
    p_19 = Decimal('0')  # Podstawa 23%
    p_20 = Decimal('0')  # Podatek 23%
    p_21 = Decimal('0')  # WDT
    p_22 = Decimal('0')  # Eksport
    p_23 = Decimal('0')  # WNT - podstawa
    p_24 = Decimal('0')  # WNT - podatek
    p_25 = Decimal('0')  # Import art. 33a - podstawa
    p_26 = Decimal('0')  # Import art. 33a - podatek
    """
    if ewidencja.imp:
      p_27=ewidencja.imp
      p_28=ewidencja.imp_vat
    else:
      p_27 = Decimal('0')  # Import usług - podstawa
      p_28 = Decimal('0')  # Import usług - podatek
    """
    p_27 = Decimal('0')  # Import usług - podstawa
    p_28 = Decimal('0')  # Import usług - podatek
    p_29 = Decimal('0')  # Import usług od podatników VAT - podstawa
    p_30 = Decimal('0')  # Import usług od podatników VAT - podatek
    p_31 = Decimal('0')  # Dostawa art. 17 ust. 1 pkt 5 - podstawa
    p_32 = Decimal('0')  # Dostawa art. 17 ust. 1 pkt 5 - podatek

    # Sumowanie z wierszy sprzedaży
    for w in ewidencja.sprzedaz_wiersze:
      # Pola K_10-K_34
      p_10 += getattr(w, 'k_10', Decimal('0')) or Decimal('0')
      p_11 += getattr(w, 'k_11', Decimal('0')) or Decimal('0')
      p_13 += getattr(w, 'k_13', Decimal('0')) or Decimal('0')
      p_15 += getattr(w, 'k_15', Decimal('0')) or Decimal('0')
      p_16 += getattr(w, 'k_16', Decimal('0')) or Decimal('0')
      p_17 += getattr(w, 'k_17', Decimal('0')) or Decimal('0')
      p_18 += getattr(w, 'k_18', Decimal('0')) or Decimal('0')
      p_19 += getattr(w, 'k_19', Decimal('0')) or Decimal('0')
      p_20 += getattr(w, 'k_20', Decimal('0')) or Decimal('0')
      p_21 += getattr(w, 'k_21', Decimal('0')) or Decimal('0')
      p_22 += getattr(w, 'k_22', Decimal('0')) or Decimal('0')
      p_23 += getattr(w, 'k_23', Decimal('0')) or Decimal('0')
      p_24 += getattr(w, 'k_24', Decimal('0')) or Decimal('0')
      p_25 += getattr(w, 'k_25', Decimal('0')) or Decimal('0')
      p_26 += getattr(w, 'k_26', Decimal('0')) or Decimal('0')
      p_27 += getattr(w, 'k_27', Decimal('0')) or Decimal('0')
      p_28 += getattr(w, 'k_28', Decimal('0')) or Decimal('0')
      p_29 += getattr(w, 'k_29', Decimal('0')) or Decimal('0')
      p_30 += getattr(w, 'k_30', Decimal('0')) or Decimal('0')
      p_31 += getattr(w, 'k_31', Decimal('0')) or Decimal('0')
      p_32 += getattr(w, 'k_32', Decimal('0')) or Decimal('0')

    # ========== PODATEK NALICZONY ==========
    p_39 = self.przeniesienie
    p_40 = Decimal('0')  # Środki trwałe - netto
    p_41 = Decimal('0')  # Środki trwałe - VAT
    p_42 = Decimal('0')  # Pozostałe - netto
    p_43 = Decimal('0')  # Pozostałe - VAT

    # Sumowanie z wierszy zakupów
    for w in ewidencja.zakup_wiersze:
      p_40 += getattr(w, 'k_40', Decimal('0')) or Decimal('0')
      p_41 += getattr(w, 'k_41', Decimal('0')) or Decimal('0')
      p_42 += getattr(w, 'k_42', Decimal('0')) or Decimal('0')
      p_43 += getattr(w, 'k_43', Decimal('0')) or Decimal('0')
    p_40 = round(p_40)
    p_41 = round(p_41)
    p_42 = round(p_42)
    p_43 = round(p_43)

    # ========== OBLICZENIA ==========
    """
    # łącznie podstawy:
    p_37=
     P_10,
P_11, P_13, P_15, P_17, P_19, P_21, P_22, P_23, P_25, P_27, P_29,
P_31

P_39=
Wysokość nadwyżki podatku naliczonego nad należnym z poprzedniej
deklaracji (pole opcjonalne).
Wykazuje się kwotę z P_62 z poprzedniej deklaracji lub kwotę
wynikającą z decyzji.
W przypadku braku - pole pozostaje puste.

p_62
Wysokość nadwyżki podatku naliczonego nad należnym do
przeniesienia na następny okres rozliczeniowy (pole opcjonalne).
W przypadku braku - pole pozostaje puste.

"""
    p_37 = p_10 + p_11 + p_13 + p_15 + p_17 + p_19 + p_21 + p_22 + p_23 + p_25 + p_27 + p_29 + p_31
    # Łączna wysokość podatku należnego (P_38)
    suma_nalezny = p_16 + p_18 + p_20 + p_24 + p_26 + p_28 + p_30 + p_32
    p_38 = round(suma_nalezny)


    # Łączna wysokość podatku naliczonego (P_48)
    p_48 = p_41 + p_43

    # Kwota do wpłaty (P_51)
    roznica = p_38 - p_48
    if roznica > Decimal('0'):
      p_51 = roznica
      p_62=0
    else:
      p_51 = Decimal('0')
      p_62=-roznica

    # Nadwyżka podatku naliczonego nad należnym (P_53)
    if p_51 == Decimal('0'):
      p_53 = abs(roznica)
    else:
      p_53 = Decimal('0')

    # ========== TWORZENIE OBIEKTU ==========
    pozycje = PozycjeSzczegolowe(
      # Podatek należny
      p_10=p_10 if p_10 > 0 else None,
      p_11=p_11 if p_11 > 0 else None,
      p_13=p_13 if p_13 > 0 else None,
      p_15=p_15 if p_15 > 0 else None,
      p_16=p_16 if p_16 > 0 else None,
      p_17=p_17 if p_17 > 0 else None,
      p_18=p_18 if p_18 > 0 else None,
      p_19=p_19 if p_19 > 0 else None,
      p_20=p_20 if p_20 > 0 else None,
      p_21=p_21 if p_21 > 0 else None,
      p_22=p_22 if p_22 > 0 else None,
      p_23=p_23 if p_23 > 0 else None,
      p_24=p_24 if p_24 > 0 else None,
      p_25=p_25 if p_25 > 0 else None,
      p_26=p_26 if p_26 > 0 else None,
      p_27=p_27 if p_27 > 0 else None,
      p_28=p_28 if p_28 > 0 else None,
      p_29=p_29 if p_29 > 0 else None,
      p_30=p_30 if p_30 > 0 else None,
      p_31=p_31 if p_31 > 0 else None,
      p_32=p_32 if p_32 > 0 else None,
      p_39=p_39 if p_39 > 0 else None,

      # Podatek naliczony
      p_40=p_40 if p_40 > 0 else None,
      p_41=p_41 if p_41 > 0 else None,
      p_42=p_42 if p_42 > 0 else None,
      p_43=p_43 if p_43 > 0 else None,
      p_48=p_48 if p_48 > 0 else None,

      # Rozliczenie
      p_37=p_37,
      p_38=p_38,
      p_51=p_51,
      p_53=p_53 if p_53 > 0 else None,
      p_62=p_62 if p_62 > 0 else None,

    )

    # Nagłówek deklaracji
    naglowek = DeklaracjaNaglowek()

    # Deklaracja
    deklaracja = Deklaracja(
      naglowek=naglowek,
      pozycje_szczegolowe=pozycje,
      pouczenia=1
    )

    return deklaracja

  def generate_jpk(self,
                   include_deklaracja: bool = True,
                   include_ewidencja: bool = True) -> Jpk:
    """Główna metoda generująca JPK"""

    # 1. Nagłówek
    naglowek = Naglowek(
      data_wytworzenia_jpk=datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
      cel_zlozenia=self.cel_zlozenia,
      kod_urzedu=self.kod_urzedu,
      rok=self.year,
      miesiac=self.month
    )

    # 2. Podmiot
    podmiot1 = self._get_podmiot()

    # 3. Ewidencja
    ewidencja = None
    deklaracja = None

    if include_ewidencja:
      sprzedaz_wiersze,total_sprzedaz = self._get_sprzedaz_data()
      zakup_wiersze, total_zakup, total_sprzedaz = self._get_zakup_data(sprzedaz_wiersze,total_sprzedaz)

      # Oblicz sumy kontrolne
      sprzedaz_ctrl = {
        "LiczbaWierszySprzedazy": len(sprzedaz_wiersze),
        "PodatekNalezny": sum([
          (getattr(w, 'k_16', Decimal('0')) or Decimal('0')) +
          (getattr(w, 'k_18', Decimal('0')) or Decimal('0')) +
          (getattr(w, 'k_20', Decimal('0')) or Decimal('0')) +
          (getattr(w, 'k_24', Decimal('0')) or Decimal('0')) +
          (getattr(w, 'k_26', Decimal('0')) or Decimal('0')) +
          (getattr(w, 'k_28', Decimal('0')) or Decimal('0')) +
          (getattr(w, 'k_30', Decimal('0')) or Decimal('0')) +
          (getattr(w, 'k_32', Decimal('0')) or Decimal('0'))
          for w in sprzedaz_wiersze])
      }

      zakup_ctrl = {
        "LiczbaWierszyZakupow": len(zakup_wiersze),
        "PodatekNaliczony": sum([
          getattr(w, 'k_41', Decimal('0')) or Decimal('0') +
          getattr(w, 'k_43', Decimal('0')) or Decimal('0')
          for w in zakup_wiersze])
      }

      ewidencja = Ewidencja(
        sprzedaz_wiersze=sprzedaz_wiersze,
        sprzedaz_ctrl=sprzedaz_ctrl,
        zakup_wiersze=zakup_wiersze,
        zakup_ctrl=zakup_ctrl,
        przeniesienie=self.przeniesienie,
        #imp = total_imp,
        #imp_vat=total_imp_vat
      )

      # 4. Deklaracja (na podstawie ewidencji)
      if include_deklaracja:
        deklaracja = self._calculate_deklaracja(ewidencja)

    # 5. Zbuduj główny obiekt JPK
    jpk = Jpk(
      naglowek=naglowek,
      podmiot1=podmiot1,
      deklaracja=deklaracja,
      ewidencja=ewidencja
    )

    return jpk

  def _build_xml_structure(self, data: Dict) -> Dict:
    """Zbuduj strukturę XML zgodną ze schematem XSD"""
    # Ta metoda powinna przekształcić dict na strukturę zgodną z XSD
    # Implementacja zależy od wymagań konkretnego XML
    return data

  def export_to_xml(self, jpk: Jpk) -> str:
    return jpk_to_xml(jpk,False)


################ XML


def _format_value(val: Any) -> str:
  if isinstance(val, Decimal):
    return f"{val:.2f}"
  if isinstance(val, (int, float)):
    return f"{val:.2f}" if isinstance(val, float) else str(val)
  if isinstance(val, date):
    return val.isoformat()
  return str(val)


def _get_xml_tag(field_name: str) -> str:
  """Mapuje nazwy pól zachowując poprawne wielkości liter dla XSD."""
  exact_tags = {
    "GTU_01", "GTU_02", "GTU_03", "GTU_04", "GTU_05", "GTU_06", "GTU_07", "GTU_08", "GTU_09",
    "GTU_10", "GTU_11", "GTU_12", "GTU_13",
    "WSTO_EE", "IED", "TP", "TT_WNT", "TT_D", "MR_T", "MR_UZ",
    "I_42", "I_63", "B_SPV", "B_SPV_DOSTAWA", "B_MPV_PROWIZJA"
  }
  if field_name.upper() in exact_tags:
    return field_name.upper()

  if field_name.lower().startswith(('p_', 'k_')):
    return field_name.upper()

  # Obsługa specjalnych przypadków
  overrides = {
    "p_ordzu": "P_ORDZU",
    "nip": "NIP",
    "email": "Email"
  }
  if field_name.lower() in overrides:
    return overrides[field_name.lower()]

  parts = field_name.split('_')
  return "".join(p.capitalize() for p in parts)


def jpk_to_xml(jpk: Jpk, pretty_print: bool = True) -> str:
  ns = "http://crd.gov.pl/wzor/2025/12/19/14090/"
  etd_ns = "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2022/09/13/eD/DefinicjeTypy/"

  #ET.register_namespace('tns', ns)
  ET.register_namespace('', ns)
  ET.register_namespace('etd', etd_ns)

  root = ET.Element(f"{{{ns}}}JPK")

  # ================= 1. NAGŁÓWEK =================
  naglowek = ET.SubElement(root, f"{{{ns}}}Naglowek")
  kf = ET.SubElement(naglowek, f"{{{ns}}}KodFormularza", {
    "kodSystemowy": jpk.naglowek.kod_systemowy,
    "wersjaSchemy": jpk.naglowek.wersja_schemy
  })
  kf.text = jpk.naglowek.kod_formularza

  ET.SubElement(naglowek, f"{{{ns}}}WariantFormularza").text = str(jpk.naglowek.wariant_formularza)
  ET.SubElement(naglowek, f"{{{ns}}}DataWytworzeniaJPK").text = str(
    jpk.naglowek.data_wytworzenia_jpk)

  if jpk.naglowek.nazwa_systemu:
    ET.SubElement(naglowek, f"{{{ns}}}NazwaSystemu").text = jpk.naglowek.nazwa_systemu

  ET.SubElement(naglowek, f"{{{ns}}}CelZlozenia", {"poz": "P_7"}).text = jpk.naglowek.cel_zlozenia
  ET.SubElement(naglowek, f"{{{ns}}}KodUrzedu").text = jpk.naglowek.kod_urzedu
  ET.SubElement(naglowek, f"{{{ns}}}Rok").text = str(jpk.naglowek.rok)
  ET.SubElement(naglowek, f"{{{ns}}}Miesiac").text = str(jpk.naglowek.miesiac)

  # ================= 2. PODMIOT1 =================
  podmiot = ET.SubElement(root, f"{{{ns}}}Podmiot1", {"rola": jpk.podmiot1.rola})

  if jpk.podmiot1.osoba_fizyczna:
    of = ET.SubElement(podmiot, f"{{{ns}}}OsobaFizyczna")
    data = jpk.podmiot1.osoba_fizyczna.model_dump(exclude_none=True)
    for f in jpk.podmiot1.osoba_fizyczna.model_fields.keys():
      if f in data:
        # Pola identyfikacyjne w OsobaFizyczna są z przestrzeni ETD
        ns_prefix = etd_ns if f in ('nip', 'imie_pierwsze', 'nazwisko', 'data_urodzenia') else ns
        ET.SubElement(of, f"{{{ns_prefix}}}{_get_xml_tag(f)}").text = _format_value(data[f])

  elif jpk.podmiot1.osoba_niefizyczna:
    onf = ET.SubElement(podmiot, f"{{{ns}}}OsobaNiefizyczna")
    data = jpk.podmiot1.osoba_niefizyczna.model_dump(exclude_none=True)
    for f in jpk.podmiot1.osoba_niefizyczna.model_fields.keys():
      if f in data:
        # W OsobaNiefizyczna wszystko jest w TNS
        ET.SubElement(onf, f"{{{ns}}}{_get_xml_tag(f)}").text = _format_value(data[f])

  # ================= 3. DEKLARACJA =================
  if jpk.deklaracja:
    deklaracja = ET.SubElement(root, f"{{{ns}}}Deklaracja")
    dekl_nag = ET.SubElement(deklaracja, f"{{{ns}}}Naglowek")
    ET.SubElement(dekl_nag, f"{{{ns}}}KodFormularzaDekl", {
      "kodSystemowy": jpk.deklaracja.naglowek.kod_systemowy,
      "kodPodatku": jpk.deklaracja.naglowek.kod_podatku,
      "rodzajZobowiazania": jpk.deklaracja.naglowek.rodzaj_zobowiazania,
      "wersjaSchemy": jpk.deklaracja.naglowek.wersja_schemy
    }).text = jpk.deklaracja.naglowek.kod_formularza_dekl
    ET.SubElement(dekl_nag, f"{{{ns}}}WariantFormularzaDekl").text = "23"

    poz_szczeg = ET.SubElement(deklaracja, f"{{{ns}}}PozycjeSzczegolowe")
    ps_data = jpk.deklaracja.pozycje_szczegolowe.model_dump(exclude_none=True)

    # XSD wymaga pełnych par dla podatków i podstaw opodatkowania
    ps_pairs = [('p_11', 'p_12'), ('p_13', 'p_14'), ('p_15', 'p_16'), ('p_17', 'p_18'),
                ('p_19', 'p_20'),
                ('p_23', 'p_24'), ('p_25', 'p_26'), ('p_27', 'p_28'), ('p_29', 'p_30'),
                ('p_31', 'p_32'),
                ('p_40', 'p_41'), ('p_42', 'p_43'), ('p_68', 'p_69')]
    for p1, p2 in ps_pairs:
      if p1 in ps_data or p2 in ps_data:
        ps_data.setdefault(p1, Decimal('0.00'))
        ps_data.setdefault(p2, Decimal('0.00'))

    # Iteracja po polach modelu gwarantuje bezbłędną kolejność XSD
    for f in jpk.deklaracja.pozycje_szczegolowe.model_fields.keys():
      if f in ps_data:
        tag = "P_ORDZU" if f == "p_ORDZU" else f.upper()
        if tag>='P_11' and tag<='P_69':
          ET.SubElement(poz_szczeg, f"{{{ns}}}{tag}").text =f"{ps_data[f]:.0f}"
        else:
          ET.SubElement(poz_szczeg, f"{{{ns}}}{tag}").text = _format_value(ps_data[f])

    ET.SubElement(deklaracja, f"{{{ns}}}Pouczenia").text = str(jpk.deklaracja.pouczenia)

  # ================= 4. EWIDENCJA =================
  if jpk.ewidencja:
    ewidencja = ET.SubElement(root, f"{{{ns}}}Ewidencja")
    k_pairs_sprzedaz = [('k_15', 'k_16'), ('k_17', 'k_18'), ('k_19', 'k_20'), ('k_23', 'k_24'),
                        ('k_25', 'k_26'), ('k_27', 'k_28'), ('k_29', 'k_30'), ('k_31', 'k_32')]
    k_pairs_zakup = [('k_40', 'k_41'), ('k_42', 'k_43')]

    # SPRZEDAŻ
    for wiersz in jpk.ewidencja.sprzedaz_wiersze:
      sw = ET.SubElement(ewidencja, f"{{{ns}}}SprzedazWiersz")
      w_data = wiersz.model_dump(exclude_none=True)

      for p1, p2 in k_pairs_sprzedaz:
        if p1 in w_data or p2 in w_data:
          w_data.setdefault(p1, Decimal('0.00'))
          w_data.setdefault(p2, Decimal('0.00'))
      typ=w_data.get('typ_dokumentu', '')
      for f in wiersz.model_fields.keys():
        # Wstrzyknięcie wymaganego typu dokumentu (jeśli brak w modelu) we właściwym miejscu
        if f in w_data:
          val = w_data[f]
          if f == 'nr_kontrahenta' and not str(val).strip():
            val = "BRAK"
          if f=='typ_dokumentu':
            if val:
              ET.SubElement(sw, f"{{{ns}}}TypDokumentu").text = val
          elif f == 'ksef_numer':
            if val:
              ET.SubElement(sw, f"{{{ns}}}NrKSeF").text = val
            else:
              if typ in ('WEW',):
                ET.SubElement(sw, f"{{{ns}}}DI").text = "1"
              else:
                ET.SubElement(sw, f"{{{ns}}}BFK").text = "1"  # Domyślnie faktura
          elif f == 'podmiot_powiazany':
            if val:
              ET.SubElement(sw, f"{{{ns}}}TP").text = '1'
          elif f == 'TIN':
            if val:
              ET.SubElement(sw, f"{{{ns}}}KodKrajuNadaniaTIN").text = val
          else:
            ET.SubElement(sw, f"{{{ns}}}{_get_xml_tag(f)}").text = _format_value(val)

        """
        NrKSeF - Numer identyfikujący fakturę w
        Krajowym Systemie e-Faktur;
        OFF - Faktura, o której mowa w art. 106nf ust.
        1 ustawy, która na dzień złożenia ewidencji nie
        posiada numeru identyfikującego tę fakturę w
        Krajowym Systemie e-Faktur;
        BFK - Faktura elektroniczna lub faktura w
        postaci papierowej;
        DI - Dowód inny niż faktura.
        """


    if jpk.ewidencja.sprzedaz_ctrl:
      sc = ET.SubElement(ewidencja, f"{{{ns}}}SprzedazCtrl")
      for k, v in jpk.ewidencja.sprzedaz_ctrl.items():
        tag = 'LiczbaWierszySprzedazy' if k.lower().replace('_',
                                                            '') == 'liczbawierszysprzedazy' else \
          'PodatekNalezny' if k.lower().replace('_', '') == 'podateknalezny' else _get_xml_tag(k)
        ET.SubElement(sc, f"{{{ns}}}{tag}").text = _format_value(v)

    # ZAKUP
    for wiersz in jpk.ewidencja.zakup_wiersze:
      zw = ET.SubElement(ewidencja, f"{{{ns}}}ZakupWiersz")
      w_data = wiersz.model_dump(exclude_none=True)

      for p1, p2 in k_pairs_zakup:
        if p1 in w_data or p2 in w_data:
          w_data.setdefault(p1, Decimal('0.00'))
          w_data.setdefault(p2, Decimal('0.00'))

      for f in wiersz.model_fields.keys():
        if f in w_data:
          val = w_data[f]
          if f == 'nr_dostawcy' and not str(val).strip():
            val = "BRAK"
          if f == 'ksef_numer':
            if val:
              ET.SubElement(zw, f"{{{ns}}}NrKSeF").text = val
            else:
              ET.SubElement(zw, f"{{{ns}}}BFK").text = "1"  # Domyślnie faktura
          elif f == 'TIN':
            if val:
              ET.SubElement(zw, f"{{{ns}}}KodKrajuNadaniaTIN").text = val
          else:
            ET.SubElement(zw, f"{{{ns}}}{_get_xml_tag(f)}").text = _format_value(val)


    if jpk.ewidencja.zakup_ctrl:
      zc = ET.SubElement(ewidencja, f"{{{ns}}}ZakupCtrl")
      for k, v in jpk.ewidencja.zakup_ctrl.items():
        tag = 'LiczbaWierszyZakupow' if k.lower().replace('_', '') == 'liczbawierszyzakupow' else \
          'PodatekNaliczony' if k.lower().replace('_', '') == 'podateknaliczony' else _get_xml_tag(
            k)
        ET.SubElement(zc, f"{{{ns}}}{tag}").text = _format_value(v)

  # ================= GENEROWANIE XML =================
  xml_str = ET.tostring(root, encoding='utf-8', xml_declaration=True)
  if pretty_print:
    parsed_xml = minidom.parseString(xml_str)
    return parsed_xml.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")

  return xml_str.decode('utf-8')

# Funkcja pomocnicza do użycia w ERPNext
@frappe.whitelist()
def generate_jpk_v7m(company: str, year: int, month: int,
           include_deklaracja: bool = True,
           include_ewidencja: bool = True,
           przeniesienie : Decimal =0) -> Dict:
  """
  Funkcja wywoływana z poziomu ERPNext do generowania JPK-V7M

  Args:
    company: Nazwa firmy
    year: Rok
    month: Miesiąc
    include_deklaracja: Czy uwzględnić deklarację
    include_ewidencja: Czy uwzględnić ewidencję

  Returns:
    Dict z danymi JPK
  """
  try:
    generator = JPK_V7M_Generator(
      company=company,
      year=int(year),
      month=int(month),
      przeniesienie=przeniesienie
    )

    jpk = generator.generate_jpk(
      include_deklaracja=include_deklaracja,
      include_ewidencja=include_ewidencja
    )

    # Konwertuj do dict
    #result = jpk.model_dump(exclude_none=True)
    result=jpk_to_xml(jpk,True)
    # Dodaj informację o sukcesie
    result["success"] = True
    result["message"] = _("JPK-V7M wygenerowany pomyślnie")

    return result

  except ValidationError as e:
    frappe.log_error(f"Błąd walidacji JPK: {str(e)}")
    return {
      "success": False,
      "message": _("Błąd walidacji danych: {0}").format(str(e)),
      "errors": e.errors()
    }
  except Exception as e:
    frappe.log_error(f"Błąd generowania JPK: {str(e)}")
    return {
      "success": False,
      "message": _("Błąd generowania JPK: {0}").format(str(e))
    }


@frappe.whitelist()
def export_jpk_to_xml(company: str, year: int, month: int, przeniesienie : Decimal) -> str:
  """
  Eksportuj JPK do XML

  Returns:
    XML jako string
  """
  try:
    generator = JPK_V7M_Generator(
      company=company,
      year=int(year),
      month=int(month),
      przeniesienie=przeniesienie
    )

    jpk = generator.generate_jpk(
      include_deklaracja=True,
      include_ewidencja=True
    )

    xml_data = generator.export_to_xml(jpk)

    # Zapisz do pliku (opcjonalnie)
    file_path = f"/tmp/JPK_V7M_{company}_{year}_{month:02d}.xml"
    with open(file_path, 'w', encoding='utf-8') as f:
      f.write(xml_data)

    return xml_data

  except Exception as e:
    frappe.log_error(f"Błąd eksportu JPK do XML: {str(e)}")
    raise


def jpk_v7m_xml(company_name, year, month, kod_urzedu=None, cel_zlozenia="1",
                przeniesienie=Decimal(0.0)): # "2" - korekta
  generator = JPK_V7M_Generator(
    company=company_name,
    year=year,
    month=month,
    cel_zlozenia = cel_zlozenia,
    kod_urzedu = kod_urzedu,
    przeniesienie=przeniesienie
  )
  jpk = generator.generate_jpk()
  return generator.export_to_xml(jpk)


# Funkcje do testowania
def test_generation(company_name):
  return export_jpk_to_xml(company_name,2026,1,0)

def test_generation1(company_name):
  """Funkcja testowa"""
  # Przykładowe użycie
  generator = JPK_V7M_Generator(
    company=company_name,
    year=2026,
    month=1,
    cel_zlozenia = "1",
    kod_urzedu = None
  )
  # Generuj pełne JPK
  jpk = generator.generate_jpk()
  xml_data = generator.export_to_xml(jpk)

  # Wyświetl wyniki
  print("JPK wygenerowany pomyślnie")
  print(f"Liczba wierszy sprzedaży: {len(jpk.ewidencja.sprzedaz_wiersze)}")
  print(f"Liczba wierszy zakupów: {len(jpk.ewidencja.zakup_wiersze)}")
  print(f"Podatek do zapłaty (P_38): {jpk.deklaracja.pozycje_szczegolowe.p_38}")

  return jpk


if __name__ == "__main__":
  # Testowanie bezpośrednie
  test_generation()

