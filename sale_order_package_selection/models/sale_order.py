from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    add_package_id = fields.Many2one('stock.quant.package', store=False, readonly=True,
        states={'draft': [('readonly', False)]},
        string='Add package',
        help="Add order lines from the content of the pack that will be sent")
    package_ids = fields.Many2many(
        "stock.quant.package",
        "Package",
        readonly=True,
    )

    @api.onchange("add_package_id")
    def _onchange_sale_complete_from_pack(self):
        if self.add_package_id not in self.package_ids:
            self.package_ids = [(4,  self.add_package_id.id)]
        for quant in self.add_package_id.quant_ids:
            self.order_line += self.env["sale.order.line"].new({
                "product_id": quant.product_id.id,
                "package_id": self.add_package_id.id,
                "product_uom_qty": quant.quantity ,
            })
        self.add_package_id = False

