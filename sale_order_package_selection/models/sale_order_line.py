from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    package_id = fields.Many2one(
        "stock.quant.package",
        "Package",
        copy=False,
    )

    def _prepare_procurement_values(self, group_id=False):
        vals = super()._prepare_procurement_values(group_id=group_id)
        if self.package_id:
            vals["restrict_package_id"] = self.package_id.id
        return vals
