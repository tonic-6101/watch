// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright (C) 2024-2026 Tonic

frappe.ui.form.on("FT Settings", {
	refresh(frm) {
		if (!frm.doc.enable_erpnext_bridge) return;

		frm.add_custom_button(__("Test Connection"), () => {
			frappe.call({
				method: "watch.api.erpnext_bridge.test_connection",
				callback(r) {
					if (r.message?.ok) {
						frappe.msgprint({
							title: __("Connection OK"),
							message: __("ERPNext is reachable and Timesheet access is confirmed."),
							indicator: "green",
						});
					} else {
						frappe.msgprint({
							title: __("Connection Failed"),
							message: r.message?.error || __("Unknown error"),
							indicator: "red",
						});
					}
				},
			});
		}, __("ERPNext Bridge"));

		frm.add_custom_button(__("Sync All Unsynced Entries"), () => {
			frappe.confirm(
				__("Sync all unsynced time entries to ERPNext now?"),
				() => {
					frappe.call({
						method: "watch.api.erpnext_bridge.bulk_sync",
						freeze: true,
						freeze_message: __("Syncing entries to ERPNext…"),
						callback(r) {
							const { days_synced, errors } = r.message || {};
							if (errors?.length) {
								frappe.msgprint({
									title: __("Sync completed with errors"),
									message: errors.join("<br>"),
									indicator: "orange",
								});
							} else {
								frappe.msgprint({
									title: __("Sync complete"),
									message: __("{0} day(s) synced.").replace("{0}", days_synced ?? 0),
									indicator: "green",
								});
							}
							frm.reload_doc();
						},
					});
				}
			);
		}, __("ERPNext Bridge"));
	},
});
