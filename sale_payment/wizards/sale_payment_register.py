# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class SalePaymentRegister(models.TransientModel):
    _name = "sale.payment.register"
    _description = "Register a payment from a sale order"

    partner_id = fields.Many2one("res.partner", required=True)
    journal_id = fields.Many2one(
        "account.journal", required=True, domain="[('type', 'in', ('bank', 'cash'))]"
    )
    payment_date = fields.Date(default=fields.Date.today(), required=True)
    communication = fields.Char()
    amount = fields.Monetary(currency_field="currency_id")
    currency_id = fields.Many2one(
        "res.currency", string="Currency", help="The payment's currency."
    )
    sale_id = fields.Many2one("sale.order", required=True)
    payment_reference = fields.Char()

    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self.env.context.get("active_model") == "sale.order":
            sale = self.env["sale.order"].browse(self.env.context["active_id"])
            res["sale_id"] = sale.id
            res["currency_id"] = (sale.currency_id.id,)
            res["amount"] = sale.amount_residual
            res["communication"] = sale.name
            res["payment_reference"] = sale.reference
            res["partner_id"] = (sale.partner_id.id,)
        return res

    def _get_payment_vals(self):
        return {
            "payment_type": "inbound",
            "partner_type": "customer",
            "partner_id": self.partner_id.id,
            "destination_account_id": self.partner_id.with_company(
                self.sale_id.company_id
            ).property_account_receivable_id.id,
            "company_id": self.sale_id.company_id.id,
            "amount": self.amount,
            "currency_id": self.currency_id.id,
            "date": self.payment_date,
            "ref": self.communication,
            "journal_id": self.journal_id.id,
            "sale_id": self.sale_id.id,
            "payment_reference": self.payment_reference,
        }

    def action_create_payments(self):
        self.ensure_one()
        vals = self._get_payment_vals()
        payment = self.env["account.payment"].create(vals)
        payment.action_post()
