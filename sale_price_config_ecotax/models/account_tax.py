from odoo import _, api, fields, models


class AccountTax(models.Model):
    _inherit = "account.tax"

    def _add_tax_details_in_base_line(self, base_line, company, rounding_method=None):
        res = super()._add_tax_details_in_base_line(
            self, base_line, company, rounding_method
        )

        if base_line["product_id"].add_ecotax_to_price:
            product_id = base_line["product_id"]
            base_line["tax_details"]["rax_total_excluded_currency"] += (
                product_id.ecotax_amount or 0.0
            )
