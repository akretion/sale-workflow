# License AGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
{
    "name": "Sale price config",
    "summary": "Adds a price configuration that compute a price from a input_line",
    "version": "18.0.1.0.0",
    "category": "Manufacture",
    "website": "https://github.com/OCA/sale-workflow",
    "author": "Akretion, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": [
        "sale_mrp_bom_configurable",
    ],
    "maintainer": [
        "franzpoize",
    ],
    "data": [
        "views/sale_price_config.xml",
        "wizard/matrix_wizard.xml",
        "wizard/wizard_sale_price_change.xml",
        "security/ir.model.access.csv",
    ],
    "assets": {
        "web.assets_backend": [
            "sale_price_config/static/src/xml/matrix_table.xml",
            "sale_price_config/static/src/js/matrix_table.esm.js",
            "sale_price_config/static/src/xml/sale_price_config_change_button.xml",
            "sale_price_config/static/src/js/sale_price_config_change_button.esm.js",
            "sale_price_config/static/src/css/matrix_table.scss",
        ],
    },
    "installable": True,
}
