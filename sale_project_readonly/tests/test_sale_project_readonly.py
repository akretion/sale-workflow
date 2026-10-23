# Copyright 2026  Akretion (https://www.akretion.com).
# @author Sébastien Alix <sebastien.alix@akretion.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl)

from odoo import Command

from odoo.addons.base.tests.common import BaseCommon


class TestSaleProjectReadonly(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group_user = cls.env.ref("base.group_user")
        cls.group_sales_readonly = cls.env.ref(
            "sales_team_readonly.group_sales_readonly"
        )
        cls.group_project_readonly = cls.env.ref(
            "project_readonly.group_project_readonly"
        )

        cls.partner = cls.env["res.partner"].create({"name": "Test Customer"})
        cls.product = cls.env["product.product"].create(
            {
                "name": "Service Product",
                "type": "service",
                "list_price": 100.0,
                "service_tracking": "project_only",
            }
        )
        cls.order = cls.env["sale.order"].create(
            {
                "partner_id": cls.partner.id,
                "order_line": [
                    Command.create(
                        {"product_id": cls.product.id, "product_uom_qty": 1.0}
                    ),
                ],
            }
        )
        cls.order.action_confirm()
        cls.project = cls.order.project_ids

        cls.user_sale_readonly = cls.env["res.users"].create(
            {
                "name": "Sales Readonly",
                "login": "sale_project_readonly_sale",
                "group_ids": [
                    Command.link(cls.group_user.id),
                    Command.link(cls.group_sales_readonly.id),
                ],
            }
        )
        cls.user_sale_project_readonly = cls.env["res.users"].create(
            {
                "name": "Sales Project Readonly",
                "login": "sale_project_readonly_user",
                "group_ids": [
                    Command.link(cls.group_user.id),
                    Command.link(cls.group_sales_readonly.id),
                    Command.link(cls.group_project_readonly.id),
                ],
            }
        )

    def _form_arch(self, user):
        return self.env["sale.order"].with_user(user).get_view(view_type="form")["arch"]

    def test_projects_button_visibility(self):
        self.assertIn(
            "action_view_project_ids",
            self._form_arch(self.user_sale_project_readonly),
        )
        self.assertNotIn(
            "action_view_project_ids",
            self._form_arch(self.user_sale_readonly),
        )

    def test_project_field_visibility(self):
        self.assertIn(
            'name="project_id"',
            self._form_arch(self.user_sale_project_readonly),
        )
        self.assertNotIn(
            'name="project_id"',
            self._form_arch(self.user_sale_readonly),
        )

    def test_readonly_user_can_read_project_fields(self):
        values = self.order.with_user(self.user_sale_project_readonly).read(
            ["project_id", "project_count", "tasks_count"]
        )[0]
        self.assertEqual(values["project_id"][0], self.project.id)
        self.assertEqual(values["project_count"], 1)
        self.assertEqual(values["tasks_count"], 0)

    def test_readonly_user_can_open_projects_action(self):
        action = self.order.with_user(
            self.user_sale_project_readonly
        ).action_view_project_ids()
        self.assertEqual(action["res_model"], "project.task")
        self.assertEqual(action["context"]["default_project_id"], self.project.id)
