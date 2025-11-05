from odoo import models


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _price_compute(
        self, price_type, uom=None, currency=None, company=None, date=False
    ):
        prices = super()._price_compute(price_type, uom, currency, company, date)

        price_config = self.env.context.get("price_config")
        input_line = self.env.context.get("input_line")

        if price_config and input_line:
            for product in self:
                # Add ecotax amount computed by account_ecotax
                prices[product.id] = prices[product.id] + (product.ecotax_amount or 0.0)

        return prices

