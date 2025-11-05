from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    add_ecotax_to_price = fields.Boolean()
