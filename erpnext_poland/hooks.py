app_name = "erpnext_poland"
app_title = "ERPNext Poland"
app_publisher = "fundacja@galicea.org"
app_description = "ErpNext localisation for Poland"
app_email = "lab@galicea.org"
app_license = "gpl-3.0"

before_migrate = "erpnext_poland.utils.before_migrate.before_migrate_setup"

# faktura korekta
doc_events = {
  "Sales Invoice": {
   "before_validate": "erpnext_poland.overrides.sales_invoice.fix_correction_invoice",
   "on_submit":       "erpnext_poland.overrides.sales_invoice.fix_gl_for_storno"
   }
}

# status co 30 minut, zakupy raz dziennie
scheduler_events = {
    "cron": {
        "*/30 * * * *": [
            "erpnext_poland.ksef_utils.check_sent_invoices_status"
        ],
        "20 13 * * *": [
            "erpnext_poland.api.nbp.synchronizuj_kursy"
        ]
    },
    "daily": [
        "erpnext_poland.ksef_utils.register_from_ksef"
    ]
}

# JPK Znacznik Konta uwzględniajacy bilans i rzis:
options_zn = """
BILANS_A
BILANS_A_I
BILANS_A_II
BILANS_A_III
BILANS_B
BILANS_B_I
BILANS_B_II
BILANS_B_III
BILANS_B_IV
BILANS_C
BILANS_C_I
BILANS_C_II
BILANS_C_III
BILANS_C_IV
BILANS_D
BILANS_D_I
BILANS_D_II
BILANS_D_III
BILANS_D_IV
BILANS_D_V
RZiS_A
RZiS_A_I
RZiS_A_I_1
RZiS_A_I_2
RZiS_A_II
RZiS_A_II_1
RZiS_A_II_2
RZiS_B
RZiS_B_I
RZiS_B_II
RZiS_B_III
RZiS_B_IV
RZiS_B_V
RZiS_C
RZiS_C_I
RZiS_C_II
RZiS_C_III
RZiS_C_IV
RZiS_C_V
RZiS_D
RZiS_D_I
RZiS_D_II
RZiS_D_III
RZiS_E
RZiS_F
"""
# JPK Tag Podatkowy
options_tp = """
RTD
RTP
RPU
RPD
RWK
RKR
RPK
RKB
RKM
RSS
RSW
RWS
RAR
"""

# "Sales Invoice" https://chat.deepseek.com/a/chat/s/d121a2c3-7783-448f-a7b7-c0409526f304

custom_fields = {
    "Account": [
        {"label": "JPK Znacznik Konta", "fieldname": "jpk_znacznik_konta", "fieldtype": "Select", "options": "\n1\n2\n3\n4\n5\n6\n7\n8\nK_0_1\nK_0_2\nK_1_1\nK_2_1\nW_4\nW_5\nW_7", "insert_after": "account_type"},
        {"label": "JPK Tag Podatkowy", "fieldname": "jpk_podatek_tag", "fieldtype": "Select", "options": "\nK_P_D\nK_N_P\nP_P_D\nP_N_P\nR_T_D\nR_P_U", "insert_after": "jpk_znacznik_konta"},
        {"label": "JPK Pozycja Bilansu", "fieldname": "jpk_bilans_pozycja", "fieldtype": "Data", "insert_after": "jpk_podatek_tag"},
        {"label": "JPK Pozycja RZiS", "fieldname": "jpk_rzis_pozycja", "fieldtype": "Data", "insert_after": "jpk_bilans_pozycja"}
    ],
    "Sales Invoice": [
  {
   "fieldname": "jpk_ksef_tab",
   "fieldtype": "Tab Break",
   "insert_after": "connections_tab", # jest też w purchase
 
#   "insert_after": "loyalty_redemption_cost_center",
   "label": "JPK i KSeF"
  },
  {
   "fieldname": "section_jpk",
   "fieldtype": "Section Break",
   "insert_after": "jpk_ksef_tab",
   "label": "JPK"
  },
  {
   "fieldname": "section_ksef",
   "fieldtype": "Section Break",
   "insert_after": "section_jpk",
   "label": "KSeF"
  },
        # Sekcja KSeF
        {"label": "KSeF Status", "fieldname": "ksef_status", "fieldtype": "Select", "options": "\nBrak\nOczekuje\nWysłano\nZaakceptowano\nOdrzucono", "insert_after": "section_ksef"},
        {"label": "KSeF ID sesji", "fieldname": "ksef_reference_nr", "fieldtype": "Data", "read_only": 0, "insert_after": "ksef_status"},
        {"label": "KSeF numer", "fieldname": "ksef_numer", "fieldtype": "Data", "read_only": 0, "insert_after": "ksef_reference_nr"},
        {"label": "Data sprzedaży KSeF", "fieldname": "ksef_data_sprzedazy", "fieldtype": "Date", "insert_after": "ksef_numer"},
        {"label": "Data wystawienia KSeF", "fieldname": "ksef_data_wystawienia", "fieldtype": "Date", "insert_after": "ksef_data_sprzedazy"},
        {"label": "Mechanizm Podzielonej Płatności", "fieldname": "ksef_mpp", "fieldtype": "Check", "insert_after": "ksef_data_wystawienia"},
        
        # Sekcja JPK na fakturze
        {"label": "Procedura JPK", "fieldname": "jpk_procedura_vat", "fieldtype": "Select", "insert_after": "section_jpk",
          "options": "\nEE\nSW\nTP\nTT_WNT\nTT_D\nMR_T\nMR_UZ\nI_42\nI_63\nB_SPV\nB_SPV_DOSTAWA\nB_MPV_PROWIZJA" },
        {
        "label": "JPK_VAT Typ Transakcji",
        "fieldname": "jpk_vat_typ_transakcji",
        "fieldtype": "Select",
        "options": "SP\nWEW\nZAK\nIMP\nEKS\nSW\nINNE",
        "insert_after": "jpk_procedura_vat",
        #"description": "Typ transakcji dla JPK_VAT7M"
        },
        {
        "label": "JPK_VAT GTU",
        "fieldname": "jpk_vat_gtu",
        "fieldtype": "Select",
        "options": "\nGTU_01\nGTU_02\nGTU_03\nGTU_04\nGTU_05\nGTU_06\nGTU_07\nGTU_08\nGTU_09\nGTU_10\nGTU_11\nGTU_12\nGTU_13",
        "insert_after": "jpk_vat_typ_transakcji",
        "description": "Grupa Towarów i Usług"
    },
    {
        "label": "JPK_VAT IED",
        "fieldname": "jpk_vat_ied",
        "fieldtype": "Check",
        "insert_after": "jpk_vat_gtu",
        "description": "Intrastat - Dostawa towarów"
    },
    {
        "label": "JPK_VAT IED Kod Kraju",
        "fieldname": "jpk_vat_ied_kraj",
        "fieldtype": "Data",
        "insert_after": "jpk_vat_ied",
        "description": "Kod kraju dla IED (2 znaki)"
    }
    ],
    "Sales Invoice Item": [
        {"label": "Kod GTU", "fieldname": "jpk_gtu", "fieldtype": "Select", "options": "\nGTU_01\nGTU_02\nGTU_03\nGTU_04\nGTU_05\nGTU_06\nGTU_07\nGTU_08\nGTU_09\nGTU_10\nGTU_11\nGTU_12\nGTU_13", "insert_after": "description"}
    ]
}

# To samo dla Purchase Invoice
custom_fields["Purchase Invoice"] = custom_fields["Sales Invoice"].copy()

#jpk_ksef_tab = next((f for f in custom_fields["Purchase Invoice"] if f["fieldname"] == "jpk_ksef_tab"), None)
#if jpk_ksef_tab:
#     jpk_ksef_tab["inser_after"] = "write_off_cost_center"

custom_fields["Item"] = [
    {
        "label": "JPK_VAT GTU Domyślny",
        "fieldname": "jpk_vat_gtu_domyslny",
        "fieldtype": "Select",
        "options": "\nGTU_01\nGTU_02\nGTU_03\nGTU_04\nGTU_05\nGTU_06\nGTU_07\nGTU_08\nGTU_09\nGTU_10\nGTU_11\nGTU_12\nGTU_13",
        "insert_after": "taxes",
        "description": "Domyślna grupa GTU dla towaru/usługi"
    },
    {
        "label": "JPK_VAT Eksport",
        "fieldname": "jpk_vat_eksport",
        "fieldtype": "Check",
        "insert_after": "jpk_vat_gtu_domyslny",
        "description": "Towar przeznaczony na eksport"
    },
    {
        "label": "JPK_VAT SW",
        "fieldname": "jpk_vat_sw",
        "fieldtype": "Check",
        "insert_after": "jpk_vat_eksport",
        "description": "Środek Wysokoenergetyczny"
    }
]
custom_fields["Company"] = [
    {
        "label": "JPK Kod Urzędu",
        "fieldname": "jpk_kod_urzedu",
        "fieldtype": "Data",
        "insert_after": "tax_id",
        "description": "Kod urzędu skarbowego (np. 1415)"
    },
    {
        "label": "JPK REGON",
        "fieldname": "jpk_regon",
        "fieldtype": "Data",
        "insert_after": "jpk_kod_urzedu",
        "description": "Numer REGON (jeśli dotyczy)"
    },
    {
        "label": "JPK Forma Opodatkowania",
        "fieldname": "jpk_forma_opodatkowania",
        "fieldtype": "Select",
        "options": "G\nL\nR\nI",  # Generalna, Łączna, Ryczałt, Karta podatkowa
        "insert_after": "jpk_regon",
        "description": "Forma opodatkowania"
    }
]

"""
fixtures0 = [
    {"doctype": "Custom Field", "filters": [["dt", "in", ("Account", "Sales Invoice", "Purchase Invoice", "Sales Invoice Item", "Item", "Company")]],
   "sync_on_migrate": 1
},
    {
        "doctype": "Client Script",
        "filters": [["module", "in", ("KSeF","JPK")]]
    },
]
"""

fixtures = [
    # Custom Fields
    {
        "doctype": "Custom Field", 
        "filters": [["dt", "in", ("Customer", "Account", "Purchase Invoice", "Sales Invoice", "Sales Invoice Item", "Item", "Company")], #
                    ["name", "!=", "Sales Invoice-custom_month"],
                    ["name", "!=", "Purchase Invoice-workflow_state"],
                    ["name", "!=", "Purchase Invoice-custom_month"]],
        "sync_on_migrate": 1
    },
    # Definicja Workflow
    {
        "doctype": "Workflow",
        "filters": [["name", "=", "Purchase"]],
        "sync_on_migrate": 1
    },
    # Stany Workflow (np. New, Expenses, Receipt)
    {
        "doctype": "Workflow State",
        "sync_on_migrate": 1
    },
    # Akcje Workflow (np. Mark as Expense, Mark as Purchase)
    {
        "doctype": "Workflow Action Master",
        "sync_on_migrate": 1
    },
    # Client Scripts
    {
        "doctype": "Client Script",
        "filters": [["module", "in", ("KSeF", "JPK")]],
        "sync_on_migrate": 1
    }
]


""" 


# automatycznie - w zdarzeniu on_submit

doc_events = {
    "Sales Invoice": {
        #"on_submit": "erpnext_poland.api_logic.ksef_integration.send_to_ksef"
        "on_submit": "erpnext_poland.ksef_utils.send_to_ksef"  # funkcja z argumentem doc (automatycznie przekazywany)
    }
}
"""

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "erpnext_poland",
# 		"logo": "/assets/erpnext_poland/logo.png",
# 		"title": "ERPNext Poland",
# 		"route": "/erpnext_poland",
# 		"has_permission": "erpnext_poland.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/erpnext_poland/css/erpnext_poland.css"
# app_include_js = "/assets/erpnext_poland/js/erpnext_poland.js"

# include js, css files in header of web template
# web_include_css = "/assets/erpnext_poland/css/erpnext_poland.css"
# web_include_js = "/assets/erpnext_poland/js/erpnext_poland.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "erpnext_poland/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "erpnext_poland/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "erpnext_poland.utils.jinja_methods",
# 	"filters": "erpnext_poland.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "erpnext_poland.install.before_install"
# after_install = "erpnext_poland.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "erpnext_poland.uninstall.before_uninstall"
# after_uninstall = "erpnext_poland.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "erpnext_poland.utils.before_app_install"
# after_app_install = "erpnext_poland.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "erpnext_poland.utils.before_app_uninstall"
# after_app_uninstall = "erpnext_poland.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "erpnext_poland.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"erpnext_poland.tasks.all"
# 	],
# 	"daily": [
# 		"erpnext_poland.tasks.daily"
# 	],
# 	"hourly": [
# 		"erpnext_poland.tasks.hourly"
# 	],
# 	"weekly": [
# 		"erpnext_poland.tasks.weekly"
# 	],
# 	"monthly": [
# 		"erpnext_poland.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "erpnext_poland.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "erpnext_poland.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "erpnext_poland.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "erpnext_poland.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["erpnext_poland.utils.before_request"]
# after_request = ["erpnext_poland.utils.after_request"]

# Job Events
# ----------
# before_job = ["erpnext_poland.utils.before_job"]
# after_job = ["erpnext_poland.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"erpnext_poland.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

