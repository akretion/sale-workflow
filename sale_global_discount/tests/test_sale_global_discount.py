# Copyright 2020 Tecnativa - David Vidal
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from unittest.mock import patch

from odoo import exceptions
from odoo.tests import Form, tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestSaleGlobalDiscount(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass()
        cls.chart_template = chart_template_ref
        cls.env.ref("base_global_discount.group_global_discount").write(
            {"users": [(4, cls.env.user.id)]}
        )
        cls.main_company = cls.env.ref("base.main_company")
        cls.account = cls.env["account.account"].create(
            {
                "name": "Test account Global Discount",
                "code": "TEST99999",
                "account_type": "asset_current",
                "reconcile": True,
            }
        )
        cls.global_discount_obj = cls.env["global.discount"]
        cls.global_discount_1 = cls.global_discount_obj.create(
            {
                "name": "Test Discount 1",
                "sequence": 1,
                "discount_scope": "sale",
                "discount": 20,
                "account_id": cls.account.id,
            }
        )
        cls.global_discount_2 = cls.global_discount_obj.create(
            {
                "name": "Test Discount 2",
                "sequence": 2,
                "discount_scope": "sale",
                "discount": 30,
                "account_id": cls.account.id,
            }
        )
        cls.global_discount_3 = cls.global_discount_obj.create(
            {
                "name": "Test Discount 3",
                "sequence": 3,
                "discount_scope": "sale",
                "discount": 50,
                "account_id": cls.account.id,
            }
        )
        cls.pricelist = cls.env["product.pricelist"].create(
            {"name": "Public Pricelist", "sequence": 1}
        )
        cls.partner_1 = cls.env["res.partner"].create(
            {"name": "Mr. Odoo", "property_product_pricelist": cls.pricelist.id}
        )
        cls.partner_2 = cls.env["res.partner"].create(
            {"name": "Mrs. Odoo", "property_product_pricelist": cls.pricelist.id}
        )
        cls.partner_2.customer_global_discount_ids = (
            cls.global_discount_2 + cls.global_discount_3
        )
        cls.product_1 = cls.env["product.product"].create(
            {"name": "Test Product 1", "type": "service"}
        )
        cls.product_2 = cls.env["product.product"].create(
            {"name": "Test Product 2", "type": "service"}
        )
        cls.tax_group_5pc = cls.env["account.tax.group"].create(
            {"name": "Test Tax Group 5%", "sequence": 1}
        )
        cls.tax_group_15pc = cls.env["account.tax.group"].create(
            {"name": "Test Tax Group 15%", "sequence": 2}
        )
        cls.tax_1 = cls.tax_sale_a
        cls.tax_1.amount = 15.0
        cls.tax_2 = cls.tax_sale_b
        cls.tax_2.amount = 5.0
        cls.sale_journal0 = cls.env["account.journal"].create(
            {
                "name": "Sale Journal",
                "type": "sale",
                "code": "SJT0",
            }
        )
        sale_form = Form(cls.env["sale.order"])
        sale_form.partner_id = cls.partner_1
        with sale_form.order_line.new() as order_line:
            order_line.product_id = cls.product_1
            order_line.tax_id.clear()
            order_line.tax_id.add(cls.tax_1)
            order_line.tax_id.add(cls.tax_2)
            order_line.product_uom_qty = 2
            order_line.price_unit = 75
        with sale_form.order_line.new() as order_line:
            order_line.product_id = cls.product_2
            order_line.tax_id.clear()
            order_line.tax_id.add(cls.tax_1)
            order_line.tax_id.add(cls.tax_2)
            order_line.product_uom_qty = 3
            order_line.price_unit = 33.33
        cls.sale = sale_form.save()

    @staticmethod
    def get_taxes_widget_total_tax(order):
        tax_amount_total = 0.0
        for subtotal in order.tax_totals["subtotals"]:
            tax_amount_total = sum(
                tax_group["tax_amount"] for tax_group in subtotal["tax_groups"]
            )
        return tax_amount_total

    def _patch_injected_tax_amount(self, amount):
        """Emulate an amount injected on the tax base line.

        Some modules inject the tax amount instead of letting the tax compute
        it, from the document line kept as record on the base line (this is
        what ``account_ecotax_tax`` does with the ecotax lines amount).
        """
        account_tax_model = type(self.env["account.tax"])
        add_tax_details = account_tax_model._add_tax_details_in_base_line

        def _add_tax_details_in_base_line(
            tax, base_line, company, rounding_method=None
        ):
            if base_line.get("record"):
                base_line["manual_tax_amounts"] = {
                    str(base_tax.id): {"tax_amount_currency": amount}
                    for base_tax in base_line["tax_ids"]
                }
            return add_tax_details(tax, base_line, company, rounding_method)

        return patch.object(
            account_tax_model,
            "_add_tax_details_in_base_line",
            _add_tax_details_in_base_line,
        )

    def test_01_global_sale_successive_discounts(self):
        """Add global discounts to the sale order"""
        self.assertAlmostEqual(self.sale.amount_total, 299.99)
        self.assertAlmostEqual(self.sale.amount_tax, 50)
        self.assertAlmostEqual(
            self.get_taxes_widget_total_tax(self.sale), self.sale.amount_tax
        )
        self.assertAlmostEqual(self.sale.amount_untaxed, 249.99)
        # Apply a single 20% global discount
        self.sale.global_discount_ids = self.global_discount_1
        self.sale._compute_tax_totals()
        # Discount is computed over the base and global taxes are computed
        # according to it line by line with the core method
        self.assertAlmostEqual(self.sale.amount_global_discount, 50)
        self.assertAlmostEqual(self.sale.amount_untaxed, 199.99)
        self.assertAlmostEqual(self.sale.amount_untaxed_before_global_discounts, 249.99)
        self.assertAlmostEqual(self.sale.amount_total, 239.99)
        self.assertAlmostEqual(self.sale.amount_total_before_global_discounts, 299.99)
        self.assertAlmostEqual(self.sale.amount_tax, 40)
        self.assertAlmostEqual(
            self.get_taxes_widget_total_tax(self.sale), self.sale.amount_tax
        )
        # Apply an additional 30% global discount
        self.sale.global_discount_ids += self.global_discount_2
        self.sale._compute_tax_totals()
        self.assertAlmostEqual(self.sale.amount_global_discount, 110)
        self.assertAlmostEqual(self.sale.amount_untaxed, 139.99)
        self.assertAlmostEqual(self.sale.amount_untaxed_before_global_discounts, 249.99)
        self.assertAlmostEqual(self.sale.amount_total, 167.99)
        self.assertAlmostEqual(self.sale.amount_total_before_global_discounts, 299.99)
        self.assertAlmostEqual(self.sale.amount_tax, 28)
        self.assertAlmostEqual(
            self.get_taxes_widget_total_tax(self.sale), self.sale.amount_tax
        )
        # The account move should look like this
        #   credit    debit  name
        # ========  =======  ===============================================
        #      150        0  Test Product 1
        #    99.99        0  Test Product 2
        #    13.13        0  Test TAX 15%
        #     4.38        0  TAX 5%
        #        0   105.01
        #        0       75  Test Discount 2 (30.00%) - Test TAX 15%, TAX 5%
        #        0    87.49  Test Discount 3 (50.00%) - Test TAX 15%, TAX 5%
        # ========  =======  ===============================================

    def test_02_global_sale_discounts_from_partner(self):
        """Change the partner and his global discounts go to the invoice"""
        # (30% then 50%)
        self.sale.partner_id = self.partner_2
        self.sale._compute_tax_totals()
        self.assertAlmostEqual(self.sale.amount_global_discount, 162.49)
        self.assertAlmostEqual(self.sale.amount_untaxed, 87.5)
        self.assertAlmostEqual(self.sale.amount_untaxed_before_global_discounts, 249.99)
        self.assertAlmostEqual(self.sale.amount_total, 105.01)
        self.assertAlmostEqual(self.sale.amount_total_before_global_discounts, 299.99)
        self.assertAlmostEqual(self.sale.amount_tax, 17.51)
        self.assertAlmostEqual(
            self.get_taxes_widget_total_tax(self.sale), self.sale.amount_tax
        )

    def test_03_global_sale_discounts_to_invoice(self):
        """All the discounts go to the invoice"""
        self.sale.partner_id = self.partner_2
        self.sale._compute_tax_totals()
        self.sale.order_line.mapped("product_id").write({"invoice_policy": "order"})
        self.sale.action_confirm()
        move = self.sale._create_invoices()
        # Check the invoice relevant fields
        self.assertEqual(len(move.invoice_global_discount_ids), 2)
        discount_amount = sum(
            move.invoice_global_discount_ids.mapped("discount_amount")
        )
        self.assertAlmostEqual(discount_amount, 162.49)
        self.assertAlmostEqual(move.amount_untaxed_before_global_discounts, 249.99)
        self.assertAlmostEqual(move.amount_untaxed, 87.5)
        self.assertAlmostEqual(move.amount_total, 105.01)
        # Expected Journal Entry
        # credit    debit    account
        # ========  =======  =========
        #      150        0  400000 (line 1)
        #    99.99        0  400000 (line 2)
        #    13.13        0  400000 (line_tax_1)
        #     4.38        0  400000 (line_tax_2)
        #        0   105.01  121000 (Base)
        #        0       75  TEST99999 (Global discount 1)
        #        0    87.49  TEST99999 (Global discount 2)
        #   267.50   267.50  <- Balance
        line_tax_1 = move.line_ids.filtered(lambda x: x.tax_line_id == self.tax_1)
        line_tax_2 = move.line_ids.filtered(lambda x: x.tax_line_id == self.tax_2)
        self.assertAlmostEqual(line_tax_1.credit, 13.13)
        self.assertAlmostEqual(line_tax_2.credit, 4.38)
        term_line = move.line_ids.filtered(
            lambda x: x.account_id.account_type == "asset_receivable"
        )
        self.assertAlmostEqual(term_line.debit, 105.01)
        discount_lines = move.line_ids.filtered("invoice_global_discount_id")
        self.assertEqual(len(discount_lines), 2)
        self.assertAlmostEqual(sum(discount_lines.mapped("debit")), 162.49)

    def test_04_mixed_taxes(self):
        """Lines with different taxes are supported.

        A global discount must stay usable on a document mixing lines with and
        without a specific tax (the ecotax, for instance): the discount applies
        on the untaxed amount of each line, whatever its taxes.
        """
        # Line 2 (3 x 33.33) with tax 1 only, line 1 with tax 1 and tax 2
        self.sale.order_line[1].tax_id = [(6, 0, self.tax_1.ids)]
        self.sale.global_discount_ids = self.global_discount_1
        self.sale._compute_amounts()
        self.sale._compute_tax_totals()
        self.assertAlmostEqual(self.sale.amount_untaxed_before_global_discounts, 249.99)
        self.assertAlmostEqual(self.sale.amount_global_discount, 50.0)
        self.assertAlmostEqual(self.sale.amount_untaxed, 199.99)
        # 120.00 x (15% + 5%) + 79.99 x 15%
        self.assertAlmostEqual(self.sale.amount_tax, 36.0)
        self.assertAlmostEqual(self.sale.amount_total, 235.99)
        self.assertAlmostEqual(
            self.get_taxes_widget_total_tax(self.sale), self.sale.amount_tax
        )
        # One discount line per tax combination on the invoice
        self.sale.order_line.mapped("product_id").write({"invoice_policy": "order"})
        self.sale.action_confirm()
        move = self.sale._create_invoices()
        self.assertEqual(len(move.invoice_global_discount_ids), 2)
        discount_lines = move.line_ids.filtered("invoice_global_discount_id")
        self.assertEqual(len(discount_lines), 2)
        self.assertAlmostEqual(sum(discount_lines.mapped("debit")), 50.0)
        self.assertAlmostEqual(move.amount_untaxed, 199.99)
        self.assertAlmostEqual(move.amount_total, 235.99)

    def test_05_no_taxes(self):
        self.sale.order_line[1].tax_id = False
        with self.assertRaises(exceptions.UserError):
            self.sale.global_discount_ids = self.global_discount_1
            self.sale._compute_amounts()

    def test_06_discounted_line(self):
        self.sale.global_discount_ids = self.global_discount_1
        line = self.sale.order_line[0]
        line.discount = 10
        self.assertAlmostEqual(line.price_subtotal, 135)
        self.assertAlmostEqual(self.sale.amount_untaxed_before_global_discounts, 234.99)
        self.assertAlmostEqual(self.sale.amount_untaxed, 187.99)

    def test_07_bypass_global_discounts(self):
        self.sale.global_discount_ids = self.global_discount_2 + self.global_discount_3
        self.sale.order_line[0].product_id.bypass_global_discount = True
        self.assertAlmostEqual(self.sale.amount_untaxed_before_global_discounts, 249.99)
        self.assertAlmostEqual(self.sale.amount_untaxed, 185.00)
        self.assertAlmostEqual(self.sale.amount_total, 222.00)
        self.assertAlmostEqual(self.sale.amount_tax, 37.00)
        self.assertAlmostEqual(
            self.get_taxes_widget_total_tax(self.sale), self.sale.amount_tax
        )

    def test_08_global_discount_with_tax_included(self):
        tax_included = self.env["account.tax"].create(
            {
                "name": "IVA 21% included",
                "amount": 21,
                "amount_type": "percent",
                "type_tax_use": "sale",
                "price_include": True,
                "include_base_amount": True,
            }
        )
        for line in self.sale.order_line:
            line.tax_id = [(6, 0, tax_included.ids)]
        self.sale._compute_tax_totals()
        self.sale.global_discount_ids = self.global_discount_1
        self.sale._compute_tax_totals()
        self.assertTrue(self.sale.amount_tax > 0)
        self.assertTrue(
            self.sale.amount_total < self.sale.amount_total_before_global_discounts
        )
        self.assertAlmostEqual(
            self.get_taxes_widget_total_tax(self.sale), self.sale.amount_tax
        )

    def test_09_injected_tax_amount_without_global_discount(self):
        """The amounts injected on the base lines must be kept on the totals.

        Without global discount, the module must not recompute the amounts
        computed by the tax engine: doing so drops everything injected on the
        base lines by other modules (the ecotax amount, for instance).
        """
        self.assertFalse(self.sale.global_discount_ids)
        with self._patch_injected_tax_amount(100.0):
            self.sale._compute_amounts()
            self.sale._compute_tax_totals()
        # 2 lines x 2 taxes x 100.0 injected
        self.assertAlmostEqual(self.sale.amount_tax, 400.0)
        self.assertAlmostEqual(self.sale.amount_untaxed, 249.99)
        self.assertAlmostEqual(self.sale.amount_global_discount, 0.0)
        self.assertAlmostEqual(
            self.get_taxes_widget_total_tax(self.sale), self.sale.amount_tax
        )

    def test_10_injected_tax_amount_with_global_discount(self):
        """The amounts injected on the base lines survive the global discount.

        The discount applies to the untaxed amount of the line, the injected
        amount does not depend on it.
        """
        self.sale.global_discount_ids = self.global_discount_1
        with self._patch_injected_tax_amount(100.0):
            self.sale._compute_amounts()
            self.sale._compute_tax_totals()
        self.assertAlmostEqual(self.sale.amount_untaxed, 199.99)
        self.assertAlmostEqual(self.sale.amount_global_discount, 50.0)
        self.assertAlmostEqual(self.sale.amount_tax, 400.0)
        self.assertAlmostEqual(self.sale.amount_total, 599.99)
        self.assertAlmostEqual(
            self.get_taxes_widget_total_tax(self.sale), self.sale.amount_tax
        )
