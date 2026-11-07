"""Translate the stored Polish KSeF status values to the English ones.

The KSeF status custom field, the technical GTU value on Item and the item
source setting of Polish Accounting Settings used Polish option values that are
now defined in English. Existing rows keep the old values, so they are mapped
here; without this patch those documents would show an empty status.

Run on migrate (patches.txt, [post_model_sync]).
"""

import frappe

# stored value -> new option value
STATUS_MAP = {
	"Brak": "",
	"Oczekuje": "Pending",
	"Wysłano": "Sent",
	"Zaakceptowano": "Accepted",
	"Przyjęto": "Accepted",
	"Odrzucono": "Rejected",
	"Błąd": "Error",
}

ITEMS_MODE_MAP = {
	"Poprzednia faktura dostawcy": "Previous supplier invoice",
	"Pozycje z formularza KSeF": "KSeF form items",
}


def execute():
	for doctype in ("Sales Invoice", "Purchase Invoice"):
		if not frappe.db.has_column(doctype, "ksef_status"):
			continue
		for old, new in STATUS_MAP.items():
			frappe.db.sql(
				f"update `tab{doctype}` set ksef_status=%s where ksef_status=%s", (new, old)
			)

	if frappe.db.has_column("Item", "jpk_gtu"):
		frappe.db.sql("update `tabItem` set jpk_gtu='' where jpk_gtu='BRAK'")

	if frappe.db.exists("DocType", "Polish Accounting Settings"):
		current = frappe.db.get_single_value("Polish Accounting Settings", "ksef_items_mode")
		if current in ITEMS_MODE_MAP:
			frappe.db.set_single_value(
				"Polish Accounting Settings", "ksef_items_mode", ITEMS_MODE_MAP[current]
			)
