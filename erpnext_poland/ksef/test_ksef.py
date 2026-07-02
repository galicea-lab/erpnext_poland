import sys

import frappe
import os
from lxml import etree  # jeśli używasz lxml do XML

# pip install cryptography

BENCH_PATH = "/erp/erpnext-bench"
SITE_NAME = "localhost"
os.chdir(BENCH_PATH)


def ksef2send(invoice_name='FV/2026/01/00001'):
  try:
    from erpnext_poland.ksef_utils import  send_to_ksef
    send_to_ksef(invoice_name)
  except Exception as e:
  	print(e)

def ksef_prepare(invoice_name='FV/2026/07/00001'):
  try:
    from erpnext_poland.ksef.create_fa3 import generate_ksef_xml
    invoice = frappe.get_doc("Sales Invoice", invoice_name)
    # Generuj XML FA(3)
    # xml_root = create_fa3_invoice(invoice.as_dict())
    # xml_str = etree.tostring(xml_root, pretty_print=True, xml_declaration=True, encoding="UTF-8")
    xml_str= generate_ksef_xml(invoice_name)
    f=open('text.xml','wb')
    f.write(xml_str)
    f.close()
  except Exception as e:
  	print(e)

if __name__=="__main__":
  #original_cwd = os.getcwd()
  #os.chdir(BENCH_PATH)
  args = sys.argv[1:]
  choice=args[0]
  try:
    frappe.init(site=SITE_NAME, sites_path="sites")
    original_cwd = os.getcwd()
    try:
        os.chdir(os.path.join(BENCH_PATH, "sites"))
        frappe.connect()
    finally:
        os.chdir(original_cwd)
    if choice=='send':
      #ksef2send(invoice_name='FV/2026/03/00002')
      ksef_prepare(invoice_name='FV/2026/07/00001')
    elif choice=='receive':
      #register_from_ksef()
      frappe.call('erpnext_poland.ksef_utils.register_from_ksef')
    elif choice=='status':

      from erpnext_poland.ksef_utils import check_sent_invoices_status
      check_sent_invoices_status()
    else:
      ksef_prepare(invoice_name='FV/2026/03/00002')
  except Exception as e:
    print(e)
  finally:
    frappe.destroy()


