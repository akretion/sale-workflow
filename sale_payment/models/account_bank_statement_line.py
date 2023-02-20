# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    manual_sale_id = fields.Many2one("sale.order", string="Sale order", store=False)
    sale_id = fields.Many2one("sale.order")

    @api.onchange("manual_reference", "manual_delete")
    def _onchange_manual_reconcile_reference_update_manual_sale(self):
        self.ensure_one()
        data = self.reconcile_data_info.get("data", [])
        for line in data:
            if line["reference"] == self.manual_reference:
                if self.manual_delete:
                    self.update(
                        {
                            "manual_sale_id": False,
                        }
                    )
                else:
                    self.manual_sale_id = line.get("sale_id") and line["sale_id"][0]

    @api.model
    def _get_account_from_sale(self, sale):
        partner = sale.commercial_partner_id
        account = partner.property_account_receivable_id
        fp = sale.fiscal_position_id
        if account and fp:
            account = fp.map_account(account)
        return account

    @api.onchange(
        "manual_sale_id",
    )
    def _onchange_manual_reconcile_vals_sale(self):
        self.ensure_one()
        data = self.reconcile_data_info.get("data", [])
        new_data = []
        for line in data:
            if line["kind"] == "liquidity":
                partner = self.manual_sale_id.commercial_partner_id or self.partner_id
                line["partner_id"] = partner and partner.name_get()[0] or False
            if line["reference"] == self.manual_reference:
                old_sale_id = line.get("sale_id") and line["sale_id"][0]
                if old_sale_id != self.manual_sale_id.id:
                    if self.manual_sale_id:
                        partner = self.manual_sale_id.commercial_partner_id
                        account = self._get_account_from_sale(self.manual_sale_id)
                    else:
                        partner = self.partner_id
                        account = self.journal_id.suspense_account_id
                    self.manual_partner_id = partner.id or False
                    self.manual_account_id = account.id
                    sale = self.manual_sale_id
                    line.update(
                        {
                            "sale_id": sale and sale.name_get()[0] or False,
                            "partner_id": partner and partner.name_get()[0] or False,
                            "account_id": account.name_get()[0],
                        }
                    )
            new_data.append(line)
        self.reconcile_data_info = self._recompute_suspense_line(
            new_data,
            self.reconcile_data_info["reconcile_auxiliary_id"],
            self.manual_reference,
        )
        self.can_reconcile = self.reconcile_data_info.get("can_reconcile", False)

    # manage sale_id on aml at statement line creation
    def _prepare_move_line_default_vals(self, counterpart_account_id=None):
        (
            liquidity_line_vals,
            counterpart_line_vals,
        ) = super()._prepare_move_line_default_vals(
            counterpart_account_id=counterpart_account_id
        )
        if self.sale_id:
            counterpart_line_vals["sale_id"] = self.sale_id.id
        return liquidity_line_vals, counterpart_line_vals

    # manage sale_id on aml at statement line reconciliation with widget in edit mode
    def _reconcile_move_line_vals(self, line, move_id=False):
        vals = super()._reconcile_move_line_vals(line, move_id=move_id)
        if line.get("sale_id"):
            vals["sale_id"] = line["sale_id"][0]
        return vals
