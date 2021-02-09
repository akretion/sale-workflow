# Copyright 2019 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from math import fmod

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import float_compare


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    qty_warning_message = fields.Char(compute="_compute_qty_validity", store=True)
    qty_invalid = fields.Boolean(compute="_compute_qty_validity", store=True)

    sale_min_qty = fields.Float(
        string="Min Qty",
        compute="_compute_sale_restricted_qty",
        store=True,
        digits="Product Unit of Measure",
    )
    force_sale_min_qty = fields.Boolean(
        compute="_compute_sale_restricted_qty", readonly=True, store=True
    )
    sale_max_qty = fields.Float(
        string="Max Qty",
        compute="_compute_sale_restricted_qty",
        store=True,
        digits="Product Unit of Measure",
    )
    force_sale_max_qty = fields.Boolean(
        compute="_compute_sale_restricted_qty", readonly=True, store=True
    )
    sale_multiple_qty = fields.Float(
        string="Multiple Qty",
        compute="_compute_sale_restricted_qty",
        store=True,
        digits="Product Unit of Measure",
    )

    @api.depends(
        "product_id",
        "product_uom",
        "product_uom_qty",
        "sale_max_qty",
        "sale_min_qty",
        "sale_multiple_qty",
    )
    def _compute_qty_validity(self):
        for line in self:
            product_qty = line.product_uom._compute_quantity(
                line.product_uom_qty, line.product_id.uom_id
            )

            def compare(qty):
                return qty and float_compare(
                    product_qty, qty, precision_rounding=line.product_uom.rounding
                )

            message = ""
            invalid = False
            if compare(line.sale_min_qty) < 0:
                if line.force_sale_min_qty:
                    message = _("Higher quantity recommended!")
                else:
                    invalid = True
                    message = _("Higher quantity required!")
            elif compare(line.sale_max_qty) > 0:
                if self.force_sale_max_qty:
                    message = _("Lower quantity recommended!")
                else:
                    invalid = True
                    message = _("Lower quantity required!")
            if line.sale_multiple_qty:
                rest_raw = fmod(product_qty, line.sale_multiple_qty)
                rest = float_compare(
                    rest_raw, 0.00, precision_rounding=line.product_uom.rounding
                )
                if rest:
                    invalid = True
                    message += _("\nCorrect multiple of quantity required!")
            line.qty_invalid = invalid
            line.qty_warning_message = message

    @api.constrains(
        "product_uom_qty", "sale_min_qty", "sale_max_qty", "sale_multiple_qty"
    )
    def check_constraint_restricted_qty(self):
        self._compute_qty_validity()
        error_lines = self.filtered("qty_invalid")
        if error_lines:
            raise ValidationError(
                "\n".join(
                    [
                        f"{line.product_id.name} error: {line.qty_warning_message}"
                        for line in error_lines
                    ]
                )
            )

    def _get_sale_restricted_qty(self):
        """Overridable function to change qty values (ex: form stock)"""
        self.ensure_one()
        res = {
            "sale_min_qty": self.product_id.sale_min_qty,
            "force_sale_min_qty": self.product_id.force_sale_min_qty,
            "sale_max_qty": self.product_id.sale_max_qty,
            "force_sale_max_qty": self.product_id.force_sale_max_qty,
            "sale_multiple_qty": self.product_id.sale_multiple_qty,
        }
        return res

    @api.depends("product_id")
    def _compute_sale_restricted_qty(self):
        for rec in self:
            rec.update(rec._get_sale_restricted_qty())

    def button_refresh_restriction_qty(self):
        lines = self.order_id.order_line
        lines._compute_sale_restricted_qty()
        lines._compute_qty_validity()
