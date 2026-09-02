# cksef/config.py
from dataclasses import dataclass
import frappe


# 1. Czysta struktura danych (zastępuje Pydantic)

# Tryby wypełniania pozycji faktury zakupu importowanej z KSeF
ITEMS_MODE_PENDING = "KSeF-PENDING"
ITEMS_MODE_PREVIOUS = "Poprzednia faktura dostawcy"
ITEMS_MODE_XML = "Pozycje z formularza KSeF"


@dataclass
class KSeF2Settings:
	cert_pfx: str
	cert_pass: str
	nip: str
	api_url: str
	credit_to_usd:str
	item_code : str
	description : str
	default_expense_account : str
	items_mode : str = ITEMS_MODE_PENDING

@dataclass
class Settings:
	ksef2: KSeF2Settings


# 2. Fabryka do budowania ustawień Z kontekstu Frappe
def get_accounting_settings() -> Settings:
	"""Pobiera i parsuje ustawienia KSeF z bazy danych Frappe"""

	# get_doc wywołujemy TYLKO wewnątrz funkcji/metod, nigdy globalnie
	ksef_doc = frappe.get_doc("Polish Accounting Settings")

	cert_pfx_path = ""
	if ksef_doc.cert_pfx:
		cert_pfx_path = frappe.get_site_path(ksef_doc.cert_pfx.strip('/'))

	ksef_settings = KSeF2Settings(
		nip=ksef_doc.nip,
		api_url=ksef_doc.api_url,
		cert_pass=ksef_doc.get_password('cert_pass'),
		cert_pfx=cert_pfx_path,
		credit_to_usd=ksef_doc.credit_to_usd,
	  item_code = ksef_doc.item_code,
	  description = ksef_doc.description,
		default_expense_account = ksef_doc.default_expense_account,
		items_mode = getattr(ksef_doc, "ksef_items_mode", None) or ITEMS_MODE_PENDING
	)

	return Settings(ksef2=ksef_settings)

