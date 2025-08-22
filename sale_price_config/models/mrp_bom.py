from odoo import fields, models


class MrpBom(models.Model):
    _inherit = "mrp.bom"

    def get_bom_configured_data(self, input_line, quantity=1.0):
        self.ensure_one()
        result = []
        for line in self.bom_line_ids.filtered(
            lambda s: not s._should_not_be_included_in_bom(input_line)
        ):
            line_quantity = (
                line.compute_qty_from_formula(input_line)
                if line.use_formula_compute_qty
                else line.product_qty
            ) * quantity
            if line.child_bom_id:
                result = result + line.child_bom_id.get_bom_configured_data(
                    input_line, line_quantity
                )
            else:
                result.append(
                    self._compute_data_from_line_and_quantity(line, line_quantity)
                )

        return result
