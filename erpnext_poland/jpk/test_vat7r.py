import frappe
import os
from lxml import etree  # jeśli używasz lxml do XML

# pip install cryptography

BENCH_PATH = "/erp/erpnext-bench"
SITE_NAME = "localhost"

import frappe
import frappe.utils
import os
import sys

BENCH_PATH = "/erp/erpnext-bench"
SITE_NAME = "localhost"


def setup_test_environment():
  """Poprawne ustawienie środowiska testowego dla frappe"""

  # Ustaw ścieżki
  os.chdir(BENCH_PATH)
  sites_path = os.path.join(BENCH_PATH, 'sites')

  if sites_path not in sys.path:
    sys.path.insert(0, sites_path)

  # Ustaw zmienne środowiskowe
  os.environ.update({
    'FRAPPE_SITE': SITE_NAME,
    'FRAPPE_BENCH': BENCH_PATH,
  })

  # Inicjalizuj frappe
  frappe.init(site=SITE_NAME, sites_path=sites_path)
  frappe.connect()

  # Ustaw flagi testowe
  frappe.flags.in_test = True
  frappe.flags.in_install = False

  # Mockuj hooks jeśli potrzebne
  if not hasattr(frappe, 'hooks'):
    frappe.hooks = frappe._dict()

  return frappe.local


def jpkv7n_prepare():
  try:
    company_name = frappe.defaults.get_user_default("Company")
    print(f"Pobrano firmę: {company_name}")
    xml_str = frappe.call('erpnext_poland.jpk.generator.generate_vat7m.export_jpk_to_xml',
                         company=company_name,
                         year=2026,
                         month=3,
                         przeniesienie=0)
    #xml_str=test_generation(company_name)
    f=open('text.xml','w') #'wb')
    f.write(xml_str)
    f.close()
  except Exception as e:
  	print(e)

try:
  site = setup_test_environment()
  """
  frappe.init(site=SITE_NAME, sites_path="sites")
  original_cwd = os.getcwd()
  try:
      os.chdir(os.path.join(BENCH_PATH, "sites"))
      frappe.connect()
  finally:
      os.chdir(original_cwd)
  """
  jpkv7n_prepare()
except Exception as e:
	print(e)
finally:
  frappe.destroy()
