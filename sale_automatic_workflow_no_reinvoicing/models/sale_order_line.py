# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.tools import float_compare


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    full_invoiced_qty = fields.Float(
        string="Invoiced Quantity",
        compute="_compute_full_invoiced_qty",
        digits="Product Unit of Measure",
        store=True,
        help="Invoiced quantity, ignoring the refunds",
    )

    @api.depends("invoice_lines.move_id.state", "invoice_lines.quantity")
    def _compute_full_invoiced_qty(self):
        for line in self:
            qty_invoiced = 0.0
            out_invoice_lines = line._get_invoice_lines().filtered(
                lambda li: li.move_id.move_type == "out_invoice"
            )
            for invoice_line in out_invoice_lines:
                if (
                    invoice_line.move_id.state != "cancel"
                    or invoice_line.move_id.payment_state == "invoicing_legacy"
                ):
                    qty_invoiced += invoice_line.product_uom_id._compute_quantity(
                        invoice_line.quantity, line.product_uom, round=False
                    )
            line.full_invoiced_qty = qty_invoiced

    def _check_is_invoiced(self):
        self.ensure_one()
        if self.display_type or self.is_downpayment or self.product_uom_qty <= 0.0:
            return False
        if self.product_id.invoice_policy == "order":
            invoiced_base = self.product_uom_qty
        elif self.product_id.invoice_policy == "delivery" and self.qty_delivered > 0.0:
            invoiced_base = self.qty_delivered
        else:
            return False
        precision = self.env["decimal.precision"].precision_get(
            "Product Unit of Measure"
        )
        return (
            float_compare(
                self.full_invoiced_qty, invoiced_base, precision_digits=precision
            )
            >= 0
        )
