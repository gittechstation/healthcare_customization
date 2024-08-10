// Copyright (c) 2024, tech and contributors
// For license information, please see license.txt

frappe.ui.form.on("Therapy Session Entry Logs", {
    setup(frm) {
    },
    refresh(frm) {
        if (frm.doc.docstatus == 1) {
            cur_frm.add_custom_button(__('Accounting Ledger'), function () {
                frappe.route_options = {
                    voucher_no: frm.doc.name,
                    from_date: frm.doc.posting_date,
                    to_date: moment(me.frm.doc.modified).format('YYYY-MM-DD'),
                    company: frm.doc.company,
                    group_by: "Group by Voucher (Consolidated)",
                    show_cancelled_entries: frm.doc.docstatus === 2,
                    ignore_prepared_report: true
                };
                frappe.set_route("query-report", "General Ledger");
            }, __("View"));
            cur_frm.add_custom_button(__("Stock Ledger"), function () {
                frappe.route_options = {
                    voucher_no: frm.doc.name,
                    from_date: moment(frm.doc.creation).format('YYYY-MM-DD'),
                    to_date: frm.doc.posting_date,
                    company: frm.doc.company,
                    show_cancelled_entries: frm.doc.docstatus === 2,
                    ignore_prepared_report: true
                };
                frappe.set_route("query-report", "Stock Ledger");
            }, __("View"));            
        }
    },
});
frappe.ui.form.on("Therapy Session Entry Logs Item", {
    item_code(frm, cdt, cdn) {
        var d = locals[cdt][cdn];
        d.company = frm.doc.company;
        if (d.item_code) {

            return frappe.call({
                method: "healthcare_customization.healthcare_customization.doctype.therapy_session_entry_logs.therapy_session_entry_logs.get_item_details",
                args: { row: d },
                callback: function (r) {
                    console.log(r)
                    frappe.model.set_value(cdt, cdn, "rate", flt(r.message));
                },
            });
        }
    },
    rate(frm, cdt, cdn) {
        var d = locals[cdt][cdn];
        frappe.model.set_value(cdt, cdn, "amount", d.rate * d.qty);
    },
    qty(frm, cdt, cdn) {
        var d = locals[cdt][cdn];
        frappe.model.set_value(cdt, cdn, "amount", d.rate * d.qty);
    },
});

cur_frm.set_query("item_code", "items", function (doc, cdt, cdn) {
    var d = locals[cdt][cdn];
    return {
        filters: { "is_stock_item": 1 },
    };
});
cur_frm.set_query("warehouse", "items", function (doc, cdt, cdn) {
    var d = locals[cdt][cdn];
    return {
        filters: {
            "is_group": 0,
            company: cur_frm.doc.company
        },
    };
});