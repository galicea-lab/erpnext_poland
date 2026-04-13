import frappe
from .jpk.generator.generate_vat7m import jpk_v7m_xml

def d2(d):
  try:
    if len(d)==1:
      return '0'+str(d)
    else:
      return str(d)
  except:
    if d<10:
      return '0'+str(d)
    else:
      return str(d)

@frappe.whitelist()
def create_jpk_v7m(jpk_ident):
    try:
        # 1. Pobierz dokument (załóżmy, że jpk_ident to nazwa dokumentu)
        doc = frappe.get_doc("JPK_V7M", jpk_ident)

        # 2. Tutaj Twój kod generujący treść pliku JPK
        # Przykładowo:
        xml_content = jpk_v7m_xml(doc.company, int(doc.year), int(doc.month), doc.tax_office_code,
                                  cel_zlozenia='2' if  doc.is_amendment==True else '1',
                                  przeniesienie=doc.forwarded_excess_of_input_tax
                                  )

        # albo np. z pliku tymczasowego:
        # with open("/tmp/jpk_temp.xml", "r", encoding="utf-8") as f:
        #     xml_content = f.read()

        file_name = f"JPK_V7M_{doc.name}_{frappe.utils.now_datetime().strftime('%Y%m%d_%H%M')}.xml"

        # 3. Najważniejsza część – zapisujemy plik i automatycznie podpinamy jako załącznik
        file_doc = frappe.get_doc({
    "doctype": "File",
    "file_name": file_name,
    "file_url": "/private/files/" + file_name,  # będzie nadpisane
    "attached_to_doctype": doc.doctype,
    "attached_to_name": doc.name,
    "is_private": 1,
    "content": xml_content.encode("utf-8"),     # jeśli string → .encode()
    "decode": False
        })
        file_doc.insert(ignore_permissions=True)
        """
        file_doc = frappe.utils.save_file(
            fname           = file_name,                    # nazwa pliku widoczna w UI
            content         = xml_content,                  # string / bytes
            dt              = doc.doctype,                  # "TwójDocType"
            dn              = doc.name,                     # "JPK-2025-0001" itp.
            folder          = "Home/Attachments",           # opcjonalnie – domyślnie OK
            is_private      = 1,                            # 1 = prywatny, 0 = publiczny
            decode          = False                         # jeśli podajesz string/bytes → False
        )
        """
        # 4. Opcjonalnie – ładny komunikat w Activity / Comments
        doc.add_comment(
            "Attachment",
            f"Wygenerowano i dołączono plik JPK_V7M: <a href='{file_doc.file_url}'>{file_doc.file_name}</a>"
        )

        # 5. Można odświeżyć pole _attachments (czasami pomaga w UI)
        doc.set("__attachments", True)

        frappe.msgprint(
            msg = f"Plik JPK_V7M został wygenerowany i dołączony jako załącznik.<br><b>{file_doc.file_name}</b>",
            title = "Sukces",
            indicator = "green"
        )

        return {
            "status": "success",
            "file_url": file_doc.file_url,
            "file_name": file_doc.file_name
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Błąd generowania JPK_V7M")
        frappe.throw(f"Nie udało się wygenerować / zapisać pliku JPK: {str(e)}")
