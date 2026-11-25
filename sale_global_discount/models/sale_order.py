# Copyright 2020 Tecnativa - David Vidal
# Copyright 2020 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, exceptions, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    global_discount_ids = fields.Many2many(
        comodel_name="global.discount",
        string="Sale Global Discounts",
        domain="[('discount_scope', '=', 'sale'), "
        "('account_id', '!=', False), '|', "
        "('company_id', '=', company_id), ('company_id', '=', False)]",
        compute="_compute_global_discount_ids",
        store=True,
        readonly=False,
    )
    # HACK: Looks like UI doesn't behave well with Many2many fields and
    # negative groups when the same field is shown. In this case, we want to
    # show the readonly version to any not in the global discount group.
    # TODO: Check if it's fixed in future versions
    global_discount_ids_readonly = fields.Many2many(
        related="global_discount_ids",
        string="Sale Global Discounts (readonly)",
        readonly=True,
    )
    amount_global_discount = fields.Monetary(
        string="Total Global Discounts",
        compute="_compute_amounts",  # pylint: disable=C8108
        currency_field="currency_id",
        compute_sudo=True,  # Odoo core fields are storable so compute_sudo is True
        readonly=True,
        store=True,
    )
    amount_untaxed_before_global_discounts = fields.Monetary(
        string="Amount Untaxed Before Discounts",
        compute="_compute_amounts",  # pylint: disable=C8108
        currency_field="currency_id",
        compute_sudo=True,  # Odoo core fields are storable so compute_sudo is True
        readonly=True,
        store=True,
    )
    amount_total_before_global_discounts = fields.Monetary(
        string="Amount Total Before Discounts",
        compute="_compute_amounts",  # pylint: disable=C8108
        currency_field="currency_id",
        compute_sudo=True,  # Odoo core fields are storable so compute_sudo is True
        readonly=True,
        store=True,
    )

    @api.model
    def get_discounted_global(self, price=0, discounts=None):
        if not discounts:
            return price
        discounted_price = price
        for discount in discounts:
            discounted_price *= 1 - (discount / 100)
        return discounted_price

    def _check_global_discounts_sanity(self):
        """Perform a sanity check for discarding cases that will lead to
        incorrect data in discounts.
        """
        self.ensure_one()
        if not self.global_discount_ids:
            return True
        taxes_keys = {}
        for line in self.order_line.filtered(
            lambda _line: not _line.display_type
            and _line.product_id
            and not _line.product_id.bypass_global_discount
        ):
            if not line.tax_id:
                raise exceptions.UserError(
                    self.env._("With global discounts, taxes in lines are required.")
                )
            for key in taxes_keys:
                if key == line.tax_id:
                    break
                elif key & line.tax_id:
                    raise exceptions.UserError(
                        self.env._("Incompatible taxes found for global discounts.")
                    )
            else:
                taxes_keys[line.tax_id] = True

    @api.depends(
        "order_line.product_id.bypass_global_discount",
        "order_line.price_subtotal",
        "order_line.price_tax",
        "order_line.price_total",
        "global_discount_ids",
    )
    def _compute_amounts(self):
        res = super()._compute_amounts()
        for order in self:
            order._check_global_discounts_sanity()
            amount_untaxed_before_global_discounts = order.amount_untaxed
            values = {
                "amount_untaxed_before_global_discounts": (
                    amount_untaxed_before_global_discounts
                ),
                "amount_total_before_global_discounts": order.amount_total,
            }
            if order.global_discount_ids:
                tax_totals = order._get_global_discount_tax_totals()
                values.update(
                    {
                        "amount_global_discount": (
                            amount_untaxed_before_global_discounts
                            - tax_totals["base_amount_currency"]
                        ),
                        "amount_untaxed": tax_totals["base_amount_currency"],
                        "amount_tax": tax_totals["tax_amount_currency"],
                        "amount_total": tax_totals["total_amount_currency"],
                    }
                )
            else:
                # Without global discount, the amounts computed by the standard
                # tax engine are already the right ones: recomputing them here
                # would drop everything injected on the tax base lines by other
                # modules (e.g. the ecotax amount computed from the ecotax
                # lines of the document).
                values["amount_global_discount"] = 0.0
            order.update(values)
        return res

    @api.depends(
        "order_line.price_subtotal",
        "currency_id",
        "company_id",
        "payment_term_id",
        "global_discount_ids",
    )
    def _compute_tax_totals(self):
        res = super()._compute_tax_totals()
        for order in self:
            if order.global_discount_ids:
                order.tax_totals = order._get_global_discount_tax_totals()
        return res

    def _get_global_discount_base_lines(self):
        """Return the order lines as tax base lines, discounts applied.

        The global discount is applied on the untaxed amount of the line, and
        the rest of the computation is left to the tax engine, with the line
        as record: the amounts injected on the base line by other modules
        (the ecotax amount, for instance) are kept.
        """
        self.ensure_one()
        account_tax = self.env["account.tax"]
        discounts = self.global_discount_ids.mapped("discount")
        base_lines = []
        for line in self._get_priced_lines().filtered("product_id"):
            price_subtotal = line.price_subtotal
            if not line.product_id.bypass_global_discount:
                price_subtotal = self.get_discounted_global(
                    price_subtotal, discounts.copy()
                )
            base_lines.append(
                line._prepare_base_line_for_taxes_computation(
                    price_unit=price_subtotal,
                    quantity=1.0,
                    discount=0.0,
                    special_mode="total_excluded",
                )
            )
        account_tax._add_tax_details_in_base_lines(base_lines, self.company_id)
        account_tax._round_base_lines_tax_details(base_lines, self.company_id)
        return base_lines

    def _get_global_discount_tax_totals(self):
        """Return the tax totals of the order, global discounts applied."""
        self.ensure_one()
        return self.env["account.tax"]._get_tax_totals_summary(
            base_lines=self._get_global_discount_base_lines(),
            currency=self.currency_id or self.company_id.currency_id,
            company=self.company_id,
        )

    @api.depends("partner_id", "company_id")
    def _compute_global_discount_ids(self):
        for order in self:
            commercial_global_disc = (
                order.partner_id.commercial_partner_id.customer_global_discount_ids
            )
            _discounts = (
                commercial_global_disc
                if commercial_global_disc
                else order.partner_id.customer_global_discount_ids
            )
            discounts = self.env["global.discount"]
            for discount in _discounts:
                if discount.company_id == order.company_id:
                    discounts |= discount
            order.global_discount_ids = discounts

    def _prepare_invoice(self):
        invoice_vals = super()._prepare_invoice()
        if self.global_discount_ids:
            invoice_vals.update(
                {"global_discount_ids": [(6, 0, self.global_discount_ids.ids)]}
            )
        return invoice_vals
