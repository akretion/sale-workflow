# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl)

from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    # NOTE: field groups cannot be widened additively: redefining `groups`
    # with upstream values and 'group_project_readonly' added
    project_ids = fields.Many2many(
        groups=(
            "project.group_project_user,"
            "project.group_project_milestone,"
            "project_readonly.group_project_readonly"
        ),
    )
    project_count = fields.Integer(
        groups="project.group_project_user,project_readonly.group_project_readonly",
    )
    tasks_count = fields.Integer(
        groups="project.group_project_user,project_readonly.group_project_readonly",
    )
    tasks_ids = fields.Many2many(
        groups="project.group_project_user,project_readonly.group_project_readonly",
    )
    show_project_button = fields.Boolean(
        groups="project.group_project_user,project_readonly.group_project_readonly",
    )
