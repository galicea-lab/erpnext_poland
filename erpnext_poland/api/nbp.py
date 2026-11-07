import frappe
import requests


@frappe.whitelist()
def synchronizuj_kursy():
    """Pobiera kursy z NBP i zapisuje w ERPNext."""
    frappe.log_error("This is a test message from the cron job", "NBP synchronisation")
    url = "http://api.nbp.pl/api/exchangerates/tables/A/?format=json"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if data and len(data) > 0:
            table = data[0]
            effective_date = table.get("effectiveDate")
            rates = table.get("rates", [])
            
            for rate in rates:
                currency_code = rate.get("code")
                exchange_rate = rate.get("mid")
                
                # Tu logika zapisu do Twojego DocType
                # ...
            
            frappe.db.commit()
            frappe.logger().info(f"NBP exchange rate synchronisation finished: {len(rates)} currencies")
            
    except Exception as e:
        frappe.log_error(title="NBP exchange rate synchronisation error", message=str(e))
