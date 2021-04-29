# Copyright (C) 2016  Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    sale_id = fields.Many2one("sale.order", string="Sales Order")

    def _prepare_move_line_default_vals(self, write_off_line_vals=None):
        vals_list = super()._prepare_move_line_default_vals(
            write_off_line_vals=write_off_line_vals
        )
        if not self.sale_id:
            return vals_list
        for vals in vals_list:
            # receivable line
            if vals.get("account_id") == self.destination_account_id.id:
                vals["sale_id"] = self.sale_id.id
        return vals_list
