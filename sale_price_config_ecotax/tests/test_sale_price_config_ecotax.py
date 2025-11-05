from odoo.tests.common import TransactionCase


class TestSalePriceConfigEcotax(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ProductTemplate = cls.env["product.template"]
        cls.ProductProduct = cls.env["product.product"]
        cls.PriceConfig = cls.env["sale.price.config"]
        cls.EcotaxClassification = cls.env["account.ecotax.classification"]
        cls.EcotaxLineProduct = cls.env["ecotax.line.product"]

        # Create a simple product
        cls.product_tmpl = cls.ProductTemplate.create(
            {
                "name": "Test Product",
                "type": "consu",
                "list_price": 0.0,
            }
        )
        cls.product = cls.product_tmpl.product_variant_id

        # Create a fixed ecotax classification (amount = 5.0)
        cls.eco_class = cls.EcotaxClassification.create(
            {
                "name": "Test Ecotax",
                "ecotax_type": "fixed",
                "default_fixed_ecotax": 5.0,
                "product_status": "M",
                "supplier_status": "MAN",
            }
        )

        # Link classification to product template via ecotax line
        cls.EcotaxLineProduct.create(
            {
                "product_tmpl_id": cls.product_tmpl.id,
                "classification_id": cls.eco_class.id,
            }
        )

        # Create a price config with no lines (base price 0.0)
        cls.price_config = cls.PriceConfig.create({"product_id": cls.product_tmpl.id})

    def test_price_includes_ecotax(self):
        # Sanity: product has computed ecotax amount of 5.0
        self.product.invalidate_recordset(["ecotax_amount"])  # ensure fresh compute
        self.assertAlmostEqual(self.product.ecotax_amount, 5.0, places=4)

        # Compute price in sale_price_config context
        prices = self.product.with_context(
            price_config=self.price_config,
            input_line=self.env["res.partner"].create({"name": "Dummy"}),
        )._price_compute("list_price")

        self.assertIn(self.product.id, prices)
        self.assertAlmostEqual(prices[self.product.id], 5.0, places=4)

