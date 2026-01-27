# Copyright 2026 Akretion (https://www.akretion.com).
# @author Raphaël Reverdy <raphael.reverdy@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountPaymentTermLine(models.Model):
    _inherit = "account.payment.term.line"

    delay_type = fields.Selection(
        selection_add=[
            ("on_sale_order_confirmation", "At order confirmation (no days)"),
            ("on_preparation", "At preparation date (no days)"),
            ("on_shipment", "At shipment date (no days)"),
        ],
        ondelete={
            "on_sale_order_confirmation": "set default",
            "on_preparation": "set default",
            "on_shipment": "set default",
        },
    )
