# Copyright 2017-20 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_compare, float_round


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    discount_fixed = fields.Float(
        string="Discount (Fixed)",
        digits="Product Price",
        help="Fixed amount discount.",
    )

    @api.constrains("discount", "discount_fixed")
    def _check_discounts(self):
        """Check that the fixed discount and the discount percentage are consistent."""
        precision = self.env["decimal.precision"].precision_get("Discount")
        for line in self:
            if line.discount_fixed and line.discount:
                calculated_fixed_discount = float_round(
                    line._get_discount_from_fixed_discount(),
                    precision_digits=precision,
                )
                if (
                    float_compare(
                        calculated_fixed_discount,
                        line.discount,
                        precision_digits=precision,
                    )
                    != 0
                ):
                    raise ValidationError(
                        _(
                            "The fixed discount %(fixed)s does not match the calculated "
                            "discount %(discount)s %%. Please correct one of the discounts."
                        )
                        % {
                            "fixed": line.discount_fixed,
                            "discount": line.discount,
                        }
                    )

    @api.depends("product_uom_qty", "discount", "price_unit", "tax_id")
    def _compute_amount(self):
        if self.discount_fixed:
            return super(
                SaleOrderLine, self.with_context({"discount_fixed": True})
            )._compute_amount()
        return super()._compute_amount()

    @api.onchange("discount_fixed", "price_unit")
    def _onchange_discount_fixed(self):
        if not self.discount_fixed:
            return

        self.discount = self._get_discount_from_fixed_discount()

    def _get_discount_from_fixed_discount(self):
        """Calculate the discount percentage from the fixed discount amount."""
        self.ensure_one()
        if not self.discount_fixed:
            return 0.0

        return (
            (self.price_unit != 0)
            and ((self.discount_fixed) / self.price_unit) * 100
            or 0.00
        )

    def _prepare_invoice_line(self, **optional_values):
        res = super()._prepare_invoice_line(**optional_values)
        res.update({"discount_fixed": self.discount_fixed})
        return res
