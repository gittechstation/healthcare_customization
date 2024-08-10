# Copyright (c) 2024, tech and contributors
# For license information, please see license.txt
import frappe
from frappe.model.document import Document
import erpnext
from frappe import _
from frappe.utils import cint, cstr, flt

from erpnext.controllers.stock_controller import create_repost_item_valuation_entry
from erpnext.stock.stock_ledger import make_sl_entries
from erpnext.controllers.selling_controller import SellingController


class TherapySessionEntryLogs(SellingController):
	def validate(self):
		total = 0.0
		for row in self.items:
			row.set("amount",  row.qty * row.rate)
			total += row.amount
		self.set("total", total)

	def on_submit(self):		
		repost_stock_entry(self)
		self.make_gl()

	def on_cancel(self):
		self.ignore_linked_doctypes = (
			"GL Entry",
			"Stock Ledger Entry",
			"Repost Item Valuation",
			"Repost Payment Ledger",
			"Repost Payment Ledger Items",
			"Repost Accounting Ledger",
			"Repost Accounting Ledger Items",
		)
		repost_stock_entry(self)
		self.make_gl()

	def make_gl(self):
		default_expense_account = frappe.db.get_value("Company", self.company, "default_expense_account")
		default_inventory_account = frappe.db.get_value("Company", self.company, "default_inventory_account")
		cost_center = frappe.db.get_value("Company", self.company, "cost_center")
		if not default_expense_account:frappe.throw(_("Set Default Cost of Goods Sold Account in Company"))
		gl_entries = []		
		gl_entries.append(
                    self.get_gl_dict(
                        {
                            "account": default_expense_account,                            
                            "due_date": self.posting_date,                            
                            "debit":self.total,
                            "debit_in_account_currency":self.total  ,
                            "against_voucher": self.name,
                            "against_voucher_type": self.doctype,
                            "voucher_type": self.doctype, 
                            "voucher_no": self.name,                           
                            "cost_center": self.cost_center or cost_center,                           
                        },                      
                        item=self,
                    )
                )
		for row in self.items:
			stock_account = frappe.db.get_value("Warehouse", row.warehouse, "account")
			if not stock_account:
				if not default_inventory_account:frappe.throw(_("Set Account in Warehouse Or Set Default Inventory Account"))
				stock_account = default_inventory_account
			
			gl_entries.append(
				self.get_gl_dict(
					{
						"account": stock_account,                            
						"due_date": self.posting_date,                            
						"credit":row.amount,
						"credit_in_account_currency":row.amount,
						"against_voucher": self.name,
						"against_voucher_type": self.doctype,
						"voucher_type": self.doctype, 
						"voucher_no": self.name,                          
					},                      
					item=self,
				)
			)

		from erpnext.accounts.general_ledger import make_gl_entries, make_reverse_gl_entries
		if self.docstatus == 1:
				make_gl_entries(
					gl_entries,					
					merge_entries=False,
					from_repost=False,
				)
		elif self.docstatus == 2:			
			make_reverse_gl_entries(voucher_type=self.doctype, voucher_no=self.name)

def repost_stock_entry(doc):	
	sl_entries = []	
	get_sle_for_target_warehouse(doc, sl_entries)

	if sl_entries:
		try:
			if doc.docstatus == 2:
				sl_entries.reverse()
			make_sl_entries(sl_entries, False)
		except Exception:
			print(f"SLE entries not posted for the stock entry {doc.name}")
			doc.log_error("Stock respost failed")


def get_sle_for_target_warehouse(doc, sl_entries):
	for d in doc.get("items"):
		if cstr(d.warehouse):
			sle = doc.get_sl_entries(
				d,
				{
					"warehouse": cstr(d.warehouse),
					"actual_qty": flt(d.qty),
					"incoming_rate": flt(d.rate),
				},
			)

			sle.recalculate_rate = 1
			sl_entries.append(sle)



import json
@frappe.whitelist()
def get_item_details(row):
	if isinstance(row, str):
		row = json.loads(row)
	row = frappe._dict(row)
	from erpnext.stock.stock_ledger import get_valuation_rate
	rate = get_valuation_rate(
					row.item_code,
					row.warehouse,
					row.parent_type,
					row.parent,
					1,
					currency=erpnext.get_company_currency(row.company),
					company=row.company				
				)
	return rate
