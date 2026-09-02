import frappe
import requests


@frappe.whitelist()
def synchronizuj_kursy():
    """Pobiera kursy z NBP i zapisuje w ERPNext."""
    frappe.log_error("To jest testowa wiadomość z zadania cron", "Synchronizacja NBP")
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
            frappe.logger().info(f"Synchronizacja kursów NBP zakończona: {len(rates)} walut")
            
    except Exception as e:
        frappe.log_error(title="Błąd synchronizacji kursów NBP", message=str(e))
