# Copyright 2018  Acsone SA/NV (http://www.acsone.eu)
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Benoît GUILLOT <benoit.guillot@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from collections import defaultdict
import datetime

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from odoo.tools import float_compare, float_round
import odoo.addons.decimal_precision as dp

_logger = logging.getLogger(__name__)


class SalePromotionRule(models.Model):
    _name = "sale.promotion.rule"
    _description = "Sale Promotion Rule"

    sequence = fields.Integer(default=10)
    used = fields.Boolean(default=False, copy=False)
    rule_type = fields.Selection(
        selection=[("coupon", "Coupon"), ("auto", "Automatic")],
        required=True,
        default="coupon",
    )
    name = fields.Char(required=True, translate=True)
    code = fields.Char()
    promo_type = fields.Selection(
        selection=[
            # ('gift', 'Gift'), TODO implement
            ("discount", "Discount"),
        ],
        required=True,
        default="discount",
    )
    discount_amount = fields.Float(
        digits=dp.get_precision("Discount"), required=True
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Discount Amount Currency",
        default=lambda a: a._get_default_currency_id(),
        oldname="discount_amount_currency_id",
    )
    discount_type = fields.Selection(
        selection=[
            ("percentage", "Percentage"),
            ("amount_tax_included", "Amount (Taxes included)"),
            ("amount_tax_excluded", "Amount (Taxes excluded)"),
        ],
        required=True,
        default="percentage",
    )
    discount_product_id = fields.Many2one(
        "product.product",
        string="Product used to apply the promotion",
        domain=[("type", "=", "service")],
    )
    date_from = fields.Date()
    date_to = fields.Date()
    only_newsletter = fields.Boolean()
    restrict_partner_ids = fields.Many2many(
        comodel_name="res.partner",
        relation="discount_rule_partner_rel",
        column1="rule_id",
        column2="partner_id",
        string="Restricted partners",
    )
    restrict_pricelist_ids = fields.Many2many(
        comodel_name="product.pricelist",
        relation="discount_rule_pricelist_rel",
        column1="rule_id",
        column2="pricelist_id",
        string="Restricted pricelists",
    )
    usage_restriction = fields.Selection(
        selection=[
            ("one_per_partner", "One per partner"),
            ("no_restriction", "No restriction"),
            ("valid_once", "One usage"),
            ("max_budget", "Maximum budget"),
        ],
        default="no_restriction",
        required=True,
    )
    minimal_amount = fields.Float(digits=dp.get_precision("Discount"))
    is_minimal_amount_tax_incl = fields.Boolean(
        "Tax included into minimal amount?", default=True, required=True
    )
    multi_rule_strategy = fields.Selection(
        selection=[
            ("use_best", "Use the best promotion"),
            ("cumulate", "Cumulate promotion"),
            ("exclusive", "Exclusive promotion"),
            ("keep_existing", "Keep existing discount"),
        ],
        default="use_best",
        description="""
It's possible to apply multiple promotions to a sale order. In such a case
the rules will be applied in the sequence order.
If the first applicable rule is 'exclusice' the process will only apply
this rule. Otherwise the process will loop over each rule and apply it
according to the strategy
""",
    )

    count_usage = fields.Integer(
        string="Number of use",
        help="Total number sale order which use this rule",
        compute="_calc_count_usage",
    )
    budget_spent = fields.Monetary(
        "Budget Spent", compute="_calc_budget_spent"
    )
    budget_max = fields.Monetary("Budget Max")

    def _get_order_promotions_considered_used_domain(self):
        """
        This functions allows to declare for which sale order state you want to
        consider the promotions in it as used. For instance when the SO is
        confirmed or when it is still a draft.
        """
        return expression.normalize_domain(
            [("state", "in", ["sale", "done"]),]
        )

    def _calc_count_usage(self):
        for rec in self:
            count = self.env["sale.order.line"].search_count(
                expression.AND(
                    [
                        self._get_order_promotions_considered_used_domain(),
                        [
                            "|",
                            ("promotion_rule_ids", "in", rec.ids),
                            ("coupon_promotion_rule_id", "=", rec.id),
                        ],
                    ]
                )
            )
            rec.count_usage = count

    def _calc_budget_spent(self):
        for rec in self:
            lines = self.env["sale.order.line"].search(
                expression.AND(
                    [
                        self._get_order_promotions_considered_used_domain(),
                        [("promotion_rule_id", "=", rec.id),],
                    ]
                )
            )
            if lines:
                if rec.discount_type == "amount_tax_included":
                    rec.budget_spent = -sum(lines.mapped("price_total"))
                else:
                    rec.budget_spent = -sum(lines.mapped("price_subtotal"))
                if rec.usage_restriction == "max_budget":
                    rec.discount_amount = rec.budget_max - rec.budget_spent

    _sql_constraints = [
        ("code_unique", "UNIQUE (code)", _("Discount code must be unique !"))
    ]

    def _get_lines_excluded_from_total_amount(self, order):
        # Excludes itself
        return order.order_line.filtered(lambda l: l.promotion_rule_id == self)

    @api.constrains("discount_product_id", "promo_type", "discount_type")
    def _check_promotion_product_id(self):
        for record in self:
            if record.promo_type != "discount":
                continue
            if record.discount_type not in (
                "amount_tax_included",
                "amount_tax_excluded",
            ):
                continue
            if not record.discount_product_id:
                raise ValidationError(
                    _(
                        "You must specify a promotion product for discount rule "
                        "applying a specific amount"
                    )
                )

    @api.constrains("promo_type", "discount_type", "currency_id")
    def _check_currency_id(self):
        for record in self:
            if record.promo_type != "discount":
                continue
            if record.discount_type not in (
                "amount_tax_included",
                "amount_tax_excluded",
            ):
                continue
            if not record.currency_id:
                raise ValidationError(
                    _(
                        "You must specify a currency for discount rule applying "
                        "a specific amount"
                    )
                )

    def _get_default_currency_id(self):
        return self.env.user.company_id.currency_id.id

    def _check_valid_partner_list(self, order):
        self.ensure_one()
        return (
            not self.restrict_partner_ids
            or order.partner_id.id in self.restrict_partner_ids.ids
        )

    def _check_valid_pricelist(self, order):
        self.ensure_one()
        return (
            not self.restrict_pricelist_ids
            or order.pricelist_id.id in self.restrict_pricelist_ids.ids
        )

    def _check_valid_newsletter(self, order):
        self.ensure_one()
        return not self.only_newsletter or not order.partner_id.opt_out

    def _check_valid_date(self, order):
        self.ensure_one()
        return not (
            (self.date_to and fields.Date.today() > self.date_to)
            or (self.date_from and fields.Date.today() < self.date_from)
        )

    def _get_valid_total_amount(self, order):
        self.ensure_one()
        excluded_lines = self._get_lines_excluded_from_total_amount(order)
        included_lines = order.order_line - excluded_lines
        amount = 0
        for line in included_lines:
            # we need to ignore already applied promotions
            taxes = line.tax_id.compute_all(
                line.price_unit,
                line.order_id.currency_id,
                line.product_uom_qty,
                product=line.product_id,
                partner=line.order_id.partner_shipping_id,
            )
            if self.is_minimal_amount_tax_incl:
                amount += taxes["total_included"]
            else:
                amount += taxes["total_excluded"]
        return amount

    def _check_valid_total_amount(self, order):
        precision = self.env["decimal.precision"].precision_get("Discount")
        return (
            float_compare(
                self.minimal_amount,
                self._get_valid_total_amount(order),
                precision_digits=precision,
            )
            < 0
        )

    @api.multi
    def check_used(self):
        for record in self:
            record.used = False
            record._calc_count_usage()
            record._calc_budget_spent()
            if record.usage_restriction == "one_per_partner":
                if record.restrict_partner_ids and record.count_usage >= len(
                    record.restrict_partner_ids
                ):
                    record.used = True
            if record.usage_restriction == "valid_once":
                if record.count_usage >= 1:
                    record.used = True
            if record.usage_restriction == "max_budget":
                if record.budget_spent >= record.budget_max:
                    record.used = True
            # remove used promotions on pending sale orders
            if record.used:
                so_lines = self.env["sale.order.line"].search(
                    [
                        ("state", "not in", ["sale", "done"]),
                        "|",
                        ("promotion_rule_ids", "in", record.ids),
                        ("coupon_promotion_rule_id", "=", record.id),
                    ]
                )
                if record.rule_type == "coupon":
                    so_lines.mapped("order_id").write(
                        {"coupon_promotion_rule_id": False,}
                    )
                else:
                    so_lines.mapped("order_id").write(
                        {"promotion_rule_ids": [(3, record.id, 0)],}
                    )
                record._remove_promotions_lines(so_lines)

    def _check_valid_usage(self, order):
        self.ensure_one()
        if self.usage_restriction == "one_per_partner":
            rule_in_use = self.env["sale.order.line"].search(
                    expression.AND([self._get_order_promotions_considered_used_domain(),
                [
                    ("order_id", "!=", order.id),
                    ("order_id.partner_id", "=", order.partner_id.id),
                    "|",
                    ("promotion_rule_ids", "in", self.id),
                    ("coupon_promotion_rule_id", "=", self.id),
                ]
            ]))
            # Do not count itself in used rules
            return len(rule_in_use - self._get_lines_excluded_from_total_amount(order)) == 0
        if self.usage_restriction in ["valid_once", "max_budget"]:
            return not self.used
        return True

    def _check_valid_multi_rule_strategy(self, order):
        self.ensure_one()
        if self.multi_rule_strategy == "exclusive":
            return len(order.mapped("order_line").mapped("applied_promotion_rule_ids") - self) == 0
        return True

    def _check_valid_rule_type(self, order):
        self.ensure_one()
        if self.rule_type == "coupon":
            return order.coupon_code is False
        return True

    @api.model
    def _get_restrictions(self):
        return [
            "date",
            "total_amount",
            "partner_list",
            "pricelist",
            "newsletter",
            "usage",
            "rule_type",
            "multi_rule_strategy",
        ]

    def _is_promotion_valid(self, order):
        self.ensure_one()
        restrictions = self._get_restrictions()
        for key in restrictions:
            if not getattr(self, "_check_valid_%s" % key)(order):
                _logger.debug("Invalid restriction %s", key)
                return False
        return True

    def _is_promotion_valid_for_line(self, line):
        precision = self.env["decimal.precision"].precision_get("Discount")
        if line.is_promotion_line:
            return False
        if self.multi_rule_strategy == "cumulate":
            return True
        if line.discount and self.multi_rule_strategy == "use_best":
            return (
                float_compare(
                    self.discount_amount,
                    line.discount,
                    precision_digits=precision,
                )
                > 0
            )
        if self.multi_rule_strategy == "keep_existing":
            return not line.discount
        return True

    @api.multi
    def name_get(self):
        res = []
        for record in self:
            if record.rule_type == "coupon":
                res.append((record.id, "%s (%s)" % (record.name, record.code)))
            elif record.rule_type == "auto":
                res.append(
                    (record.id, "%s (%s)" % (record.name, _("Automatic")))
                )
            else:
                res.extend(super(SalePromotionRule, record)._name_get())
        return res

    @api.model
    def compute_promotions(self, orders):
        """
        Compute available promotions on the given orders. If a coupon is
        already defined on the orders, it's preserved
        """
        orders_by_coupon = defaultdict(self.env["sale.order"].browse)
        for order in orders:
            orders_by_coupon[order.coupon_promotion_rule_id] += order
        # first reset (applied list only)
        self.remove_promotions(orders, remove_lines=False)
        for coupon, _orders in list(orders_by_coupon.items()):
            # coupon must be always applied first
            if coupon:
                coupon._apply(orders)
            self.apply_auto(orders)

    @api.multi
    def apply_coupon(self, orders, coupon_code):
        """Add a coupon to orders"""
        coupon_rule = self.search(
            [
                ("code", "=ilike", coupon_code),
                ("rule_type", "=", "coupon"),
                ("used", "=", False),
            ]
        )
        if not coupon_rule:
            raise UserError(_("Code number %s is invalid") % coupon_code)
        orders_without_coupon = orders.filtered(
            lambda o, c=coupon_rule: o.coupon_promotion_rule_id != coupon_rule
        )
        self.remove_promotions(orders_without_coupon)
        # coupon take precedence on auto rules
        coupon_rule._apply(orders_without_coupon)
        self.apply_auto(orders_without_coupon)

    @api.model
    def apply_auto(self, orders):
        """Apply automatic promotion rules to the orders"""
        auto_rules = self.search(
            [("rule_type", "=", "auto"), ("used", "=", False)]
        )
        auto_rules._apply(orders)

    @api.model
    def remove_promotions(self, orders, remove_lines=True):
        orders.write(
            {"promotion_rule_ids": [(5)], "coupon_promotion_rule_id": False}
        )
        if remove_lines:
            self._remove_promotions_lines(orders.mapped("order_line"))

    @api.model
    def _remove_promotions_lines(self, lines):
        lines_by_order = defaultdict(self.env["sale.order.line"].browse)
        for line in lines:
            lines_by_order[line.order_id] |= line
        # update lines from the order to avoid to trigger the compute
        # methods on each line updated. Indeed, update on a X2many field
        # is always done in norecompute on the parent...
        for order, _lines in list(lines_by_order.items()):
            vals = []
            for line in _lines:
                if line.is_promotion_line:
                    vals.append((2, line.id))
                elif line.has_promotion_rules:
                    v = {
                        "discount": 0.0,
                        "coupon_promotion_rule_id": False,
                        "promotion_rule_ids": [(5)],
                    }
                    vals.append((1, line.id, v))
            if vals:
                order.write({"order_line": vals})
                # re-Apply pricelist discount
                for line in order.order_line:
                    line._onchange_discount()

    @api.multi
    def _apply(self, orders):
        for rule in self:
            orders_valid = orders.filtered(
                lambda o, r=rule: r._is_promotion_valid(o)
            )
            orders_invalid = orders - orders_valid
            for order in orders_invalid:
                # remove itself when necessary
                self._remove_promotions_lines(order.order_line.filtered(lambda l: l.promotion_rule_id == self or l.coupon_promotion_rule_id == self or self in l.promotion_rule_ids))
            if not orders_valid:
                continue
            for order in orders_valid:
                order_line_vals = rule._apply_rule_to_order_lines(
                    order.mapped("order_line")
                )
                order_line_vals.extend(rule._apply_rule_to_orders(order))
                if rule.rule_type == "coupon":
                    order.write(
                        {
                            "coupon_promotion_rule_id": rule.id,
                            "order_line": order_line_vals,
                        }
                    )
                else:
                    order.write(
                        {
                            "promotion_rule_ids": [(4, rule.id)],
                            "order_line": order_line_vals,
                        }
                    )

    @api.multi
    def _apply_rule_to_order_lines(self, lines):
        self.ensure_one()
        lines = lines.filtered(
            lambda l, r=self: r._is_promotion_valid_for_line(l)
        )
        if self.promo_type == "discount":
            return self._apply_discount_to_order_lines(lines)
        else:
            raise ValidationError(
                _("Not supported promotion type %s") % self.promo_type
            )

    @api.multi
    def _apply_rule_to_orders(self, order):
        self.ensure_one()
        if self.promo_type == "discount":
            return self._apply_discount_to_order(order)
        else:
            raise ValidationError(
                _("Not supported promotion type %s") % self.promo_type
            )

    def _compute_percent_discount_by_lines(self, order, lines):
        self.ensure_one()
        if not order == lines.mapped("order_id"):
            raise Exception("All lines must come from the same order")
        if self.discount_type == "percentage":
            percent_by_line = dict.fromkeys(lines, self.discount_amount)
        else:
            raise ValidationError(
                _("Promotion of type %s is not a percentage discount")
                % self.discount_type
            )
        return percent_by_line

    @api.multi
    def _apply_discount_to_order_lines(self, lines):
        self.ensure_one()
        if not self.promo_type == "discount":
            return

        lines_by_order = defaultdict(self.env["sale.order.line"].browse)
        for line in lines:
            lines_by_order[line.order_id] |= line
        # update lines from the order to avoid to trigger the compute
        # methods on each line updated. Indeed, update on a X2many field
        # is always done in norecompute on the parent...
        vals = []
        for order, _lines in list(lines_by_order.items()):
            discount_by_line = {}
            if self.discount_type == "percentage":
                discount_by_line = self._compute_percent_discount_by_lines(
                    order, lines
                )
            for line in _lines:
                percent_discount = discount_by_line.get(line, 0.0)
                discount = line.discount
                if self.multi_rule_strategy != "cumulate":
                    discount = 0.0
                discount += percent_discount
                if (
                    self.rule_type == "coupon"
                    and self.discount_type == "percentage"
                ):
                    v = {
                        "discount": discount,
                        "coupon_promotion_rule_id": self.id,
                    }
                else:
                    v = {
                        "discount": discount,
                        "promotion_rule_ids": [(4, self.id)],
                    }
                vals.append((1, line.id, v))
        return vals

    @api.multi
    def _apply_discount_to_order(self, order):
        self.ensure_one()
        if not self.promo_type == "discount":
            return
        if self.discount_type in (
            "amount_tax_excluded",
            "amount_tax_included",
        ):
            lines = order.order_line.filtered(
                lambda l, r=self: r._is_promotion_valid_for_line(l)
            )
            order_line_discount_vals = self._prepare_order_line_discount(
                order, lines
            )
            existing_order_line = order.mapped("order_line").filtered(
                lambda l: l.promotion_rule_id == self
            )
            if len(existing_order_line) > 0:
                if order_line_discount_vals["price_unit"] == 0:
                    return [(6, 0, existing_order_line.id)]
                return [(1, existing_order_line.id, order_line_discount_vals)]
            else:
                if order_line_discount_vals["price_unit"] == 0:
                    return []
                return [(0, None, order_line_discount_vals)]
        return []

    @api.multi
    def _prepare_order_line_discount(self, order, lines):
        self.ensure_one()
        # takes all applied taxes
        taxes = self.discount_product_id.taxes_id
        if order.fiscal_position_id:
            taxes = order.fiscal_position_id.map_tax(taxes)
        price = self.currency_id._convert(
            from_amount=self.discount_amount,
            to_currency=order.currency_id,
            company=order.company_id,
            date=datetime.date.today(),
        )
        # Do not allow to reduce price under minimal_amount
        price = min(price, self._get_valid_total_amount(order))
        if taxes:
            price_precision_digits = self.env[
                "decimal.precision"
            ].precision_get("Product Price")
            amounts = taxes.compute_all(
                price,
                order.currency_id,
                1,
                product=self.discount_product_id,
                partner=order.partner_shipping_id,
            )

            result_discount = amounts["total_included"]
            if self.discount_type == "amount_tax_excluded":
                result_discount = amounts["total_excluded"]
            if float_compare(
                result_discount, price, precision_digits=price_precision_digits
            ):
                average_tax = 100.0 - (price / result_discount) * 100
                price += (price * -average_tax) / 100
            price = float_round(price, price_precision_digits)
            price = self._fix_discount_amount_rounding(
                price, taxes, price_precision_digits, order
            )
        return {
            "product_id": self.discount_product_id.id,
            "price_unit": -price,
            "product_uom_qty": 1,
            "promotion_rule_id": self.id,
            "is_promotion_line": True,
            "name": self.discount_product_id.name,
            "product_uom": self.discount_product_id.uom_id.id,
            "tax_id": [(4, tax.id, False) for tax in taxes],
        }

    def _fix_discount_amount_rounding(
        self, price, taxes, precision_digits, order
    ):
        """
        In this method we recompute the taxes for the given price to be sure
        that we don't have rounding issue.
        If the computed price to not match the expected discount amount, we try
        to fix the rounding issue by adding/removing the most significative
        amount according to the price decision while the computed price doesn't
        match the expected amount or the sign of the difference changes
        """
        order_amount = order.amount_total
        order_amount_untaxed = order.amount_untaxed
        for line in self._get_lines_excluded_from_total_amount(order):
            order_amount -= line.price_total
            order_amount_untaxed -= line.price_total - line.price_tax
        from_amount = min(
            self.discount_amount, order_amount - self.minimal_amount
        )
        if self.discount_type == "amount_tax_excluded":
            from_amount = min(self.discount_amount, order_amount_untaxed)
        expected_discount = self.currency_id._convert(
            from_amount=from_amount,
            to_currency=order.currency_id,
            company=order.company_id,
            date=datetime.date.today(),
        )
        amount_type = "total_included"
        if self.discount_type == "amount_tax_excluded":
            amount_type = "total_excluded"
        price_amounts = taxes.compute_all(
            price,
            order.currency_id,
            1,
            product=self.discount_product_id,
            partner=order.partner_shipping_id,
        )
        diff = float_compare(
            price_amounts[amount_type],
            expected_discount,
            precision_digits=precision_digits,
        )
        if not diff:
            return price
        while diff:
            step = 1.0 / 10 ** precision_digits
            price += step * -diff
            price_amounts = taxes.compute_all(
                price,
                order.currency_id,
                1,
                product=self.discount_product_id,
                partner=order.partner_shipping_id,
            )
            new_diff = float_compare(
                price_amounts[amount_type],
                expected_discount,
                precision_digits=precision_digits,
            )
            if not new_diff:
                return price
            if new_diff != diff:
                # not able to fix the rounding issue due to current precision
                return price

    def write(self, vals):
        res = super().write(vals)
        if any(vals.get(val) for val in ["usage_restriction", "budget_max"]):
            self.check_used()
        return res
