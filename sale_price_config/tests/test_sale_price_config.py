from odoo.tests.common import TransactionCase


class DummyInputLine:
    def _get_input_line_values(self):
        # Minimal values for check_domain to evaluate
        return {}


class TestSalePriceConfig(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ProductTemplate = cls.env["product.template"]
        cls.ProductProduct = cls.env["product.product"]
        cls.PriceConfig = cls.env["sale.price.config"]
        cls.PriceConfigLine = cls.env["sale.price.config.line"]

        # Product to price
        cls.product_tmpl = cls.ProductTemplate.create(
            {
                "name": "SPC Test Product",
                "type": "consu",
                "list_price": 0.0,
            }
        )
        cls.product = cls.product_tmpl.product_variant_id

        # Price config with a single base line (fixed amount)
        cls.price_config = cls.PriceConfig.create({"product_id": cls.product_tmpl.id})
        cls.PriceConfigLine.create(
            {
                "sale_price_config_id": cls.price_config.id,
                "line_type": "base",
                "amount": 12.0,
            }
        )

    def test_base_line_price(self):
        prices = self.product.with_context(
            price_config=self.price_config,
            input_line=DummyInputLine(),
        )._price_compute("list_price")

        self.assertIn(self.product.id, prices)
        self.assertAlmostEqual(prices[self.product.id], 12.0, places=4)

