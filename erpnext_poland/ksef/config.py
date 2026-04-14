# core/config.py
import frappe

class KSeF2Settings():
  """Model dla sekcji [ksef2]"""
  cert_pfx: str
  cert_pass: str
  nip : str
  api_url : str

  def __init__(self, **data):
    # Pobieranie całego dokumentu ustawień
    settings = frappe.get_doc("Polish Accounting Settings")
    self.nip=settings.nip
    self.api_url=settings.api_url
    # Hasło zostanie automatycznie odszyfrowane przez get_password
    self.cert_pass = settings.get_password('cert_pass')
    # settings.cert_pfx zwróci URL w postaci "/private/files/pieczec.pfx"
    # frappe.get_site_path konwertuje to na pełną ścieżkę absolutną na serwerze!
    if settings.cert_pfx:
      self.cert_pfx = frappe.get_site_path(settings.cert_pfx.strip('/'))
    else:
      self.cert_pfx = "sites/localhost/private/files/pieczec.pfx"

# --- Główna klasa ustawień, która agreguje wszystkie sekcje ---
class Settings():
  ksef2: KSeF2Settings

  def __init__(self, **data):
    self.ksef2 = KSeF2Settings()

settings=Settings()

