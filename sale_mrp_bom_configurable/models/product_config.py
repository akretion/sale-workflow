from odoo import _, fields, models
from odoo.exceptions import UserError


class InputLine(models.Model):
    _inherit = "product.config"

    order_line_id = fields.Many2one(
        comodel_name="sale.order.line", ondelete="cascade", copy=False
    )

    def write(self, vals):
        config_elements = self._get_config_elements()
        for rec in self:
            if rec.order_line_id.order_id.state == "sale":
                for field_name in config_elements:
                    if field_name in vals:
                        raise UserError(_("Can't change config when sale in confirmed"))
        res = super().write(vals)
        return res
