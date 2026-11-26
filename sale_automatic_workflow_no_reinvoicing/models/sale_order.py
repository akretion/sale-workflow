# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    no_reinvoicing = fields.Boolean(
        compute="_compute_no_reinvoicing", store=True, index=True
    )

    @api.depends(
        "order_line.full_invoiced_qty",
        "order_line.qty_delivered",
        "order_line.product_uom_qty",
    )
    def _compute_no_reinvoicing(self):
        for sale in self:
            if any(line._check_is_invoiced() for line in sale.order_line):
                sale.no_reinvoicing = True
            else:
                sale.no_reinvoicing = False
