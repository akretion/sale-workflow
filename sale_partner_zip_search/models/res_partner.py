# Copyright 2025 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class ResPartner(models.Model):
    _inherit = "res.partner"

    @property
    def _rec_names_search(self):
        return list(set(super()._rec_names_search + ["zip"]))

    def _get_complete_name(self):
        res = super()._get_complete_name()
        if self.env.context.get("show_zip") and self.zip:
            res = f"{res}, {self.zip}"
        return res.strip()
