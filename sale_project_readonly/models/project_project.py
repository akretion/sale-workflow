# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl)

from odoo import fields, models


class ProjectProject(models.Model):
    _inherit = "project.project"

    # Required for the sale order smart button: `project_ids` is computed
    # with a search on `reinvoiced_sale_order_id`.
    reinvoiced_sale_order_id = fields.Many2one(
        groups=(
            "sales_team.group_sale_salesman,sales_team_readonly.group_sales_readonly"
        ),
    )
