from odoo import api, fields, models
from odoo.fields import Command


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"
    should_compute_price = fields.Boolean(
        compute="_compute_should_compute_price",
        store=True,
        precompute=True,
        default=False,
    )

    def _compute_should_compute_price(self):
        return (
            "_compute_should_compute_price must be overriden."
            + "It should set should_compute_price to True and "
            + "depend on all relevant field in input_line"
        )

    @api.depends("should_compute_price")
    def _compute_price_unit(self):
        for rec in self:
            if not rec.is_static_product:
                if rec.should_compute_price:
                    rec = rec.with_context(
                        price_config=rec.product_id.product_tmpl_id._find_price_config(),
                        input_line=rec.input_line_id,
                    )
                    rec.should_compute_price = False
                    super(SaleOrderLine, rec)._compute_price_unit()
            else:
                super(SaleOrderLine, rec)._compute_price_unit()
        return True
