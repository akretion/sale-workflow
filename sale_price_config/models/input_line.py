from odoo import api, fields, models


class Inputline(models.Model):
    _inherit = "input.line"

    def _get_valid_components(self):
        self.ensure_one()
        return self.bom_id.get_bom_configured_data(self)

    def create_bom_line_data(self):
        self.ensure_one()
        components = self._get_valid_components()
        return components
