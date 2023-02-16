# Copyright 2014-2021 Akretion France (http://www.akretion.com)
# @author Alexis de Lattre <alexis.delattre@akretion.com>
# Copyright 2016-2021 Sodexis (http://sodexis.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProductProduct(models.Model):
    _inherit = "product.product"

    # Link rental service -> rented HW product
    rented_product_ids = fields.Many2many(
        comodel_name="product.product",
        relation="rental_product_rel",
        column1="rental_product_id",
        column2="rented_product_id",
        string="Related Rented Products",
        domain=[("type", "in", ("product", "consu"))],
    )
    # Link rented HW product -> rental service
    rental_service_ids = fields.Many2many(
        comodel_name="product.product",
        relation="rental_product_rel",
        column1="rented_product_id",
        column2="rental_product_id",
        string="Related Rental Services",
    )

    @api.constrains("rented_product_ids", "must_have_dates", "type", "uom_id")
    def _check_rental(self):
        time_uom_categ = self.env.ref("uom.uom_categ_wtime")
        for product in self:
            if product.rented_product_ids:
                if product.type != "service":
                    raise ValidationError(
                        _("The rental product '%s' must be of type 'Service'.")
                        % product.name
                    )
                if not product.must_have_dates:
                    raise ValidationError(
                        _(
                            "The rental product '%s' must have the option "
                            "'Must Have Start and End Dates' checked."
                        )
                        % product.name
                    )
                # In the future, we would like to support all time UoMs
                # but it is more complex and requires additionnal developments
                if (
                    product.rented_product_ids
                    and product.uom_id.category_id != time_uom_categ
                ):
                    raise ValidationError(
                        _(
                            "The category of the unit of measure of the rental product "
                            "'%s' must be 'Working time'."
                        )
                        % product.name
                    )


class ProductTemplate(models.Model):
    _inherit = "product.template"

    rented_product_tmpl_ids = fields.Many2many(
        "product.template",
        relation="rental_product_tmpl_rel",
        column1="rental_product_tmpl_id",
        column2="rented_product_tmpl_id",
        compute="_compute_rented_product_tmpl_ids",
        string="Rented Products",
        inverse="_inverse_rented_product_tmpl_ids",
        store=True,
    )
    rental_service_tmpl_ids = fields.Many2many(
        "product.template",
        relation="rental_product_tmpl_rel",
        column1="rental_product_tmpl_id",
        column2="rented_product_tmpl_id",
        string="Rental Services",
    )

    @api.depends("product_variant_ids", "product_variant_ids.rented_product_ids")
    def _compute_rented_product_tmpl_ids(self):
        unique_variants = self.filtered(
            lambda template: len(template.product_variant_ids) == 1
        )
        for template in unique_variants:
            template.rented_product_tmpl_ids = (
                template.product_variant_ids.rented_product_ids.product_tmpl_id.ids
            )
        for template in self - unique_variants:
            template.rented_product_tmpl_ids = False

    def _inverse_rented_product_tmpl_ids(self):
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.product_variant_ids.rented_product_ids = (
                    template.rented_product_tmpl_ids.product_variant_ids[0].ids
                )
