from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    order_line_count = fields.Integer(
        string="Order lines count", compute="_compute_order_line_count"
    )

    @api.depends("order_line")
    def _compute_order_line_count(self):
        for rec in self:
            rec.order_line_count = len(rec.order_line)

    def show_lines(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Lines",
            "view_mode": "list",
            "res_model": "product.config",
            "view_id": self.env.ref("mrp_bom_configurable.product_config_tree").id,
            "domain": [
                ("order_line_id.order_id", "=", self.id),
                ("order_line_id.is_static_product", "=", False),
            ],
        }
