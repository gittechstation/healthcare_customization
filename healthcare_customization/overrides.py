import frappe
from healthcare.healthcare.doctype.therapy_session.therapy_session import TherapySession

class CustomTherapySession(TherapySession):
    def on_submit(self):
        if self.items:
            doc = frappe.new_doc("Therapy Session Entry Logs")
            doc.posting_date = self.posting_date
            doc.posting_time = self.posting_time
            doc.transaction_date = self.transaction_date
            doc.ignore_pricing_rule = 0
            doc.company = self.company
            doc.ignore_pricing_rule = 0
            items = []
            for row in self.items:
                items.append({
                    "item_code":row.item_code,
                    "qty":row.qty,
                    "rate":row.rate,
                    "warehouse":row.warehouse,
                    "uom":row.uom,
                })
            doc.set("items", items)
            doc.insert()
            doc.submit()
            self.therapy_session_entry_logs = doc.name
            self.save()

    def on_cancel(self):
        super(CustomTherapySession, self).on_cancel()			
        self.ignore_linked_doctypes = (
            "GL Entry",
            "Stock Ledger Entry",
            "Repost Item Valuation",
            "Repost Payment Ledger",
            "Repost Payment Ledger Items",
            "Repost Accounting Ledger",
            "Repost Accounting Ledger Items",
            "Therapy Session Entry Logs"		
        )
        if self.therapy_session_entry_logs:
            frappe.get_doc("Therapy Session Entry Logs", self.therapy_session_entry_logs).cancel()