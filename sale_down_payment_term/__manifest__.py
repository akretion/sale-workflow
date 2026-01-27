# Copyright 2026 Akretion (https://www.akretion.com).
# @author Raphaël Reverdy <raphael.reverdy@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Sale down payment terms",
    "version": "18.0.1.0.0",
    "category": "Accounting/Accounting",
    "summary": "Specify amount to pay before invoicing",
    "depends": ["account", "sale_management", "sale_payment"],
    "author": " Akretion, Odoo Community Association (OCA)",
    "maintainers": ["hparfr"],
    "data": [
        "views/sale_order.xml",
    ],
    "installable": True,
    "license": "LGPL-3",
}
