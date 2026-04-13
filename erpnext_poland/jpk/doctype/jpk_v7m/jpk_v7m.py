# -*- coding: utf-8 -*-
# Copyright (c) 2021, Marcin Lewicz and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
import calendar
from frappe.model.document import Document
from frappe.utils import flt


class JPK_V7M(Document):

	def autoname(self):
		"""
		Set custom document name, including:
		- company abbreviation,
		- year,
		- month
		- 1 (if first upload) or consecutive number (if it's amendment)
		"""

		partial_name = self.abbr + "-" + self.year + "-" + "{:02d}".format(int(self.month)) + "-"

		other_docs = frappe.get_all("JPK_V7M",
			fields=['name'],
			filters={'name': ['like', partial_name + "%"]}
		)

		num_of_docs = len(other_docs)

		if self.is_amendment == "No":
			self.consecutive_number = 1
		elif num_of_docs > 1:
			self.consecutive_number = num_of_docs + 1
		else:
			# Omit "1" if it is amendment
			# because "1" will mean "original" JPK_V7M
			self.consecutive_number = 2

		self.name = partial_name + str(self.consecutive_number)


	@frappe.whitelist()
	def get_jpk(self,
		is_guidance_accepted,
		purpose,
		tax_office_code,
		year,
		month,
		is_natural_person,
		first_name,
		last_name,
		date_of_birth,
		full_name,
		tax_number,
		email,
		phone,
		forwarded_excess_of_input_tax,
		amendment_reasons
	):
		"""
		Main method, calling functions for gathering processed documents
		data and creating JPK_V7M xml file.
		"""

		file_name = "JPK_V7M-" + self.name + ".xml"
		file_path_short = "/private/files/" + file_name
		file_path = frappe.local.site + file_path_short
		app_name = "ERPNext " + frappe.get_module("erpnext").__version__

		create_jpk(
			is_guidance_accepted,
			purpose,
			tax_office_code,
			year,
			month,
			is_natural_person,
			first_name,
			last_name,
			date_of_birth,
			full_name,
			tax_number,
			email,
			phone,
			forwarded_excess_of_input_tax,
			input_tax_documents,
			output_tax_documents,
			amendment_reasons,
			app_name,
			file_path
		)

		new_file = frappe.get_doc({
			'doctype': 'File',
			'attached_to_doctype': self.doctype,
			'attached_to_name': self.name,
			'file_url': file_path_short,
			'file_name': file_name,
			'is_private': 1
		})

		new_file.insert()

		return file_name



def get_party_data(document):
	"""
	Return data of a party (customer or supplier) from given doc.
	"""

	party_name = ""
	party_type = ""
	tax_id = document.tax_id
	tax_id_short = "BRAK"
	country = ""
	country_code = ""

	if hasattr(document, "customer_name"):
		party_name = document.customer_name
		country = get_customer_country(document)
		if (not tax_id) and is_tax_id_obligatory(country):
			tax_id = get_obligatory_tax_id(document.customer_name, "Customer")
	elif hasattr(document, "supplier_name"):
		party_name = document.supplier_name
		country = get_supplier_country(document)
		if (not tax_id) and is_tax_id_obligatory(country):
			tax_id = get_obligatory_tax_id(document.supplier_name, "Supplier")

	# country codes in ERPNext are lowercase, so we have to use "upper()"
	country_code = country.code.upper()

	if tax_id:
		tax_id = tax_id.upper()
		if tax_id[0:2] == country_code:
			tax_id_short = tax_id[2:]
		else:
			tax_id_short = tax_id

	return {"name": party_name, "country_code": country_code, "tax_id": tax_id_short}


def get_customer_country(document):
	"""
	Returns Country of customer from given Purchase Invoice, or Poland if
	address not set.

	Looks for address in:
	- customer_address
	- customer.customer_primary_address
	"""

	address_name = document.shipping_address_name

	# if shipping adress is not set on document
	if not address_name:
		address_name = document.customer_address

	# if customer address is not set on document, too
	if not address_name:
		customer = frappe.get_doc("Customer", document.customer)
		address_name = customer.customer_primary_address

	return get_country_from_address(address_name, return_default = True)


def get_supplier_country(document):
	"""
	Returns Country of supplier from given document.
	"""

	# checking document.supplier_address could be omitted, but
	# someone could forget to change default country in supplier.country
	# and still set correct country in supplier_address

	address_name = document.supplier_address

	if address_name:
		return get_country_from_address(address_name)

	supplier = frappe.get_doc("Supplier", document.supplier)
	return frappe.get_doc("Country", supplier.country)


def get_country_from_address(address_name, return_default = False):
	"""
	Returns Country (doctype) according to country set in address.

	Arguments:
	- address_name: name of Address doctype
	- return_default: if True, will return default company's country name if
	country not found in address or if address_name is None
	"""

	country_name = None

	if address_name:
		address = frappe.get_doc("Address", address_name)
		country_name = address.country

	if (not country_name) and return_default:
		default_company_name = frappe.defaults.get_user_default("Company")
		default_company = frappe.get_doc("Company", default_company_name)
		country_name = default_company.country

	if country_name:
		return frappe.get_doc("Country", country_name)
	else:
		frappe.throw(_("Country name missing."))


def get_obligatory_tax_id(party_name, party_doctype_name):
	return None


def is_tax_id_obligatory(country):
	return False
