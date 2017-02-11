# -*- coding: utf-8 -*-
# © 2016 Akretion (http://www.akretion.com)
# Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Sale Team Default Value",
    "summary": "Default Value for Sale Team for populating sale order",
    "version": "8.0.1.0.0",
    "category": "sale",
    "website": "https://odoo-community.org/",
    "author": "Akretion, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "external_dependencies": {
        "python": [],
        "bin": [],
    },
    "depends": [
        "sales_team",
    ],
    "data": [
        "views/sale_team_view.xml",
    ],
    "demo": [
    ],
    "qweb": [
    ]
}
