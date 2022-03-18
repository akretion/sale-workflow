# Copyright 2017 Omar Castiñeira, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.tools import float_compare, float_is_zero


class SaleOrder(models.Model):

    _inherit = "sale.order"

    account_payment_ids = fields.One2many(
        "account.payment",
        "sale_id",
        string="Advance payments",
        compute="_compute_account_payment_ids",
        inverse="_inverse_account_payment_ids",
        store=True,
    )
    left_to_alloc = fields.Monetary(
        "Leftover to allocate",
        readonly=True,
        compute="_compute_sale_advance_payment",
        store=True,
        currency_field="currency_id",
    )
    left_to_pay = fields.Monetary(
        "Leftover to pay",
        readonly=True,
        compute="_compute_sale_advance_payment",
        store=True,
        currency_field="currency_id",
    )
    payment_line_ids = fields.Many2many(
        "account.move.line",
        string="Payment move lines",
        compute="_compute_sale_advance_payment",
        store=True,
    )
    payment_status = fields.Selection(
        selection=[
            ("not_paid", "Not Paid"),
            ("paid", "Paid"),
            ("partial", "Partially Paid"),
        ],
        string="Payment Status",
        store=True,
        readonly=True,
        copy=False,
        tracking=True,
        compute="_compute_payment_status",
    )
    is_allocated = fields.Boolean(
        string="Is allocated",
        help="True if the Order's payments (draft or posted) equals the Order's "
        "total amount",
        store=True,
        copy=False,
        tracking=True,
        default=False,
        compute="_compute_is_allocated",
    )
    keep_unposted_payments = fields.Boolean(
        string="Keep unposted payments",
        help="If checked, the unposted payments won't be deleted when creating invoice "
        "from Sale Order",
        copy=False,
    )

    @api.depends("currency_id", "left_to_alloc")
    def _compute_is_allocated(self):
        for order in self:
            pr = order.currency_id.rounding or self.env.company.currency_id.rounding
            lta = order.left_to_alloc
            order.is_allocated = float_is_zero(lta, precision_rounding=pr)

    @api.depends("currency_id", "amount_total", "left_to_pay")
    def _compute_payment_status(self):
        for order in self:
            pr = order.currency_id.rounding or self.env.company.currency_id.rounding
            amt_total = order.amount_total
            ltp = order.left_to_pay
            is_paid = float_is_zero(ltp, precision_rounding=pr)
            has_amt_paid = float_compare(amt_total, ltp, precision_rounding=pr) > 0

            if has_amt_paid:
                order.payment_status = "paid" if is_paid else "partial"
            else:
                order.payment_status = "not_paid"

    def _get_line_amount_in_order_currency(self, line_ids):
        """Returns line_ids amount in order currency.
        line_ids are AccountMoveLines related to self's invoices."""
        self.ensure_one()
        total_amount = 0
        for line in line_ids:
            line_currency = line.currency_id or line.company_id.currency_id
            line_amount = line.amount_currency if line.currency_id else line.balance
            if line_currency != self.currency_id:
                line_amount = line.currency_id._convert(
                    line_amount,
                    self.currency_id,
                    self.company_id,
                    line.date or fields.Date.today(),
                )
            total_amount += line_amount
        return total_amount

    # TODO: this depends list can be optimized
    @api.depends(
        "currency_id",
        "company_id",
        "amount_total",
        "account_payment_ids",
        "invoice_status",
        "account_payment_ids.state",
        "account_payment_ids.move_id",
        "account_payment_ids.move_id.line_ids",
        "account_payment_ids.move_id.line_ids.date",
        "account_payment_ids.move_id.line_ids.debit",
        "account_payment_ids.move_id.line_ids.credit",
        "account_payment_ids.move_id.line_ids.currency_id",
        "account_payment_ids.move_id.line_ids.amount_currency",
        "invoice_ids.line_ids.matched_debit_ids",
        "invoice_ids.state",
        "invoice_ids.payment_state",
    )
    def _compute_sale_advance_payment(self):
        for order in self:
            # 1) Amount related to advance payments
            advance_draft = 0.0
            advance_posted = 0.0
            pay_ids = order.account_payment_ids.filtered(lambda p: p.state != "cancel")
            pay_mls = pay_ids.move_id.line_ids.filtered(
                lambda x: x.account_id.internal_type == "receivable"
            )
            for pay_line in pay_mls:
                line_amount = order._get_line_amount_in_order_currency(pay_line)
                line_amount *= -1
                if pay_line.parent_state == "posted":
                    advance_posted += line_amount
                    advance_draft += line_amount
                elif pay_line.parent_state == "draft":
                    advance_draft += line_amount

            # 2) Amount related to invoices
            inv_amount = 0.0
            inv_bank_matched = 0.0
            inv_ids = order.invoice_ids.filtered(lambda i: i.state != "cancel")
            inv_mls = inv_ids.line_ids.filtered(
                lambda x: x.account_id.internal_type == "receivable"
            )
            for inv_line in inv_mls:
                inv_line_amount = order._get_line_amount_in_order_currency(inv_line)
                inv_amount += inv_line_amount
                # In case invoices are paid through bank reconciliation,
                # these payments don't create account.payment (=nothing added to
                # account_payment_ids) but we still need to calculate the amount paid.
                matched_line_ids = inv_line.matched_credit_ids.credit_move_id
                if matched_line_ids and not matched_line_ids.move_id.payment_id:
                    inv_bank_matched -= order._get_line_amount_in_order_currency(
                        matched_line_ids
                    )

            left_to_alloc = order.amount_total - max(advance_draft, inv_amount)
            left_to_pay = order.amount_total - max(advance_posted, inv_bank_matched)

            # Force order as allocated/paid if fully invoiced and/or invoices are paid.
            # Useful when invoices total amount is different from order's amount
            if order.invoice_status == "invoiced":
                left_to_alloc = 0
                if all(inv.payment_state == "paid" for inv in inv_ids):
                    left_to_pay = 0

            order.payment_line_ids = pay_mls
            order.left_to_alloc = left_to_alloc
            order.left_to_pay = left_to_pay

    @api.depends("invoice_ids.line_ids.matched_credit_ids")
    def _compute_account_payment_ids(self):
        """Add payments 'matched with the order's invoices' to the order's payments"""
        for order in self:
            matched_ids = order.invoice_ids.line_ids.matched_credit_ids
            order.account_payment_ids |= matched_ids.credit_move_id.move_id.payment_id

    def _inverse_account_payment_ids(self):
        for order in self:
            order.account_payment_ids.write({"sale_id": order.id})

    def _cancel_unlink_unposted_payments(self):
        """Cancel draft payments and delete them"""
        for order in self:
            pay_ids = order.account_payment_ids.filtered(
                lambda p: p.state in ["draft", "cancel"]
            )
            pay_ids.action_cancel()
            pay_ids.unlink()

    def _create_invoices(self, grouped=False, final=False, date=None):
        if not self.keep_unposted_payments:
            self._cancel_unlink_unposted_payments()
        return super()._create_invoices(grouped=grouped, final=final, date=date)

    def write(self, vals):
        if vals.get("state") == "cancel":
            self._cancel_unlink_unposted_payments()
        return super().write(vals)
