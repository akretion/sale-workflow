# Copyright 2026 Akretion (https://www.akretion.com).
# @author Raphaël Reverdy <raphael.reverdy@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    is_so_confirmation_amount_reached = fields.Boolean(
        compute="_compute_is_amount_reached", store=True
    )
    is_preparation_confirmation_amount_reached = fields.Boolean(
        compute="_compute_is_amount_reached", store=True
    )
    is_picking_confirmation_amount_reached = fields.Boolean(
        compute="_compute_is_amount_reached", store=True
    )

    @api.depends("payment_term_id", "amount_down_payment")
    def _compute_is_amount_reached(self):
        """Return whether `self.amount_paid` is higher than the prepayment
        required amount.
        """
        # currencies not supported
        # only for SO, we don't need sign

        for rec in self:
            total_amount = rec.amount_total
            residual_amount = total_amount
            # attention à l'ordre
            # 50% à préparation
            # 10% au shipment (en plus)
            # ça veux dire que shipment : 60% du total

            term_vals = {
                "amount_on_sale_order_confirmation": 0,
                "amount_on_preparation": 0,
                "amount_on_shipment": 0,
            }

            for i, line in enumerate(rec.payment_term_id.line_ids):
                if line.delay_type not in (
                    "on_sale_order_confirmation",
                    "on_preparation",
                    "on_shipment",
                ):
                    continue
                key = f"amount_{line.delay_type}"

                on_balance_line = i == len(rec.payment_term_id.line_ids) - 1
                if on_balance_line:
                    term_vals[key] += rec.currency_id.round(residual_amount)
                elif line.value == "fixed":
                    # Fixed amounts
                    term_vals[key] += line.value_amount
                else:
                    # Percentage amounts
                    line_amount = rec.currency_id.round(
                        total_amount * (line.value_amount / 100.0)
                    )
                    term_vals[key] += line_amount

            # order is SO, then prep, then ship
            # 50% on SO + 25% on ship
            # = 75% should be paied to unlock shippping
            on_so = term_vals["amount_on_sale_order_confirmation"]
            on_prep = on_so + term_vals["amount_on_preparation"]
            on_ship = on_prep + term_vals["amount_on_shipment"]
            compare_amounts = rec.currency_id.compare_amounts
            rec.write(
                {
                    "is_so_confirmation_amount_reached": compare_amounts(
                        on_so,
                        rec.amount_down_payment,
                    )
                    <= 0,
                    "is_picking_confirmation_amount_reached": compare_amounts(
                        on_ship,
                        rec.amount_down_payment,
                    )
                    <= 0,
                    "is_preparation_confirmation_amount_reached": compare_amounts(
                        on_prep,
                        rec.amount_down_payment,
                    )
                    <= 0,
                }
            )
