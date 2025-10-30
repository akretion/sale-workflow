from odoo import fields, models
from odoo.exceptions import UserError


class InputLine(models.Model):
    _inherit = "input.line"

    order_line_id = fields.Many2one(
        comodel_name="sale.order.line", ondelete="cascade", copy=False
    )

    def write(self, vals):
        for rec in self:
            if rec.order_line_id.order_id.state == "sale":
                for field_name in rec._get_config_elements():
                    if field_name in vals:
                        raise UserError("Can't change config when sale in confirmed")
        res = super().write(vals)
        return res
