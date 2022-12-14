# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    sale_id = fields.Many2one("sale.order", string="Sale order")


# TODO
#    def process_reconciliation(
#        self, counterpart_aml_dicts=None, payment_aml_rec=None, new_aml_dicts=None
#    ):
#        if new_aml_dicts and self.sale_id:
#            for aml_dict in new_aml_dicts:
#                aml_dict["sale_id"] = self.sale_id.id
#                aml_dict["name"] = self.sale_id.name
#        return super().process_reconciliation(
#            counterpart_aml_dicts=counterpart_aml_dicts,
#            payment_aml_rec=payment_aml_rec,
#            new_aml_dicts=new_aml_dicts,
#        )
#
#    @api.onchange("sale_id")
#    def onchange_sale_id(self):
#        if self.sale_id:
#            self.partner_id = self.sale_id.partner_id.id
