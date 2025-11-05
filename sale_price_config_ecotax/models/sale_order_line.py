from odoo import _, api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.depends("product_uom_qty", "discount", "price_unit", "tax_id")
    def _compute_amount(self):
        super()._compute_amount()

        for line in self:
            if line.product_template_id.add_ecotax_to_price:
                line.price_subtotal += line.product_id.ecotax_amount or 0.0
                line.price_tax = line.price_total - line.price_subtotal
