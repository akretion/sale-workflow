from odoo import fields, models
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def _find_price_config(self):
        price_configs = self.env["sale.price.config"].search(
            [
                "&",
                ("product_id", "=", self.id),
                (
                    "start_date",
                    "<",
                    fields.Date.context_today(self).strftime("%Y-%m-%d 00:00:00"),
                ),
                "|",
                (
                    "end_date",
                    ">",
                    fields.Date.context_today(self).strftime("%Y-%m-%d 00:00:00"),
                ),
                ("end_date", "=", False),
            ]
        )

        if len(price_configs) > 1:
            raise UserError(
                "There is more than one active price configuration for this product"
            )

        if price_configs:
            return price_configs[0]
        else:
            return False
