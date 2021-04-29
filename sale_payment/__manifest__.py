# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Sale Payment",
    "version": "14.0.1.0.0",
    "category": "Sales Management",
    "author": "Akretion,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/sale-workflow",
    "license": "AGPL-3",
    "depends": ["sale", "account_reconciliation_widget"],
    "data": [
        "security/ir.model.access.csv",
        "views/sale_order_view.xml",
        "wizards/sale_payment_register_views.xml",
        "views/account_bank_statment_views.xml",
    ],
    "installable": True,
}
