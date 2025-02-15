# Copyright (C) 2024 Akretion (<http://www.akretion.com>).
# @author Kévin Roche <kevin.roche@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    show_sale_line_warehouse_column = fields.Boolean(
        related="company_id.show_sale_line_warehouse_column",
        string="Afficher l'Entrepôt sur les lignes de commande de vente",
        readonly=False,
    )
