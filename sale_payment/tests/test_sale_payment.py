# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestSalePayment(TransactionCase):
    def setUp(self):
        super().setUp()
        self.sale = self.env.ref("sale.portal_sale_order_1")

    def test_payment_register_action_button(self):
        action = self.sale.action_register_payment()
        active_id = action.get("context", {}).get("active_id")
        self.assertEqual(active_id, self.sale.id)

    def test_add_payment_from_sale(self):
        bank_journal = self.env["account.journal"].search(
            [("type", "=", "bank")], limit=1
        )
        wizard = (
            self.env["sale.payment.register"]
            .with_context(active_id=self.sale.id, active_model="sale.order")
            .create({"journal_id": bank_journal.id, "amount": 1000})
        )
        wizard.action_create_payments()
        payment = self.sale.payment_line_ids
        self.assertEqual(len(payment), 1)
        self.assertEqual(payment.amount_currency, -1000)
        self.assertEqual(self.sale.amount_residual, 740)
        wizard = (
            self.env["sale.payment.register"]
            .with_context(active_id=self.sale.id, active_model="sale.order")
            .create({"journal_id": bank_journal.id, "amount": 740})
        )
        wizard.action_create_payments()
        self.assertEqual(len(self.sale.payment_line_ids), 2)
        self.assertEqual(self.sale.amount_residual, 0)
