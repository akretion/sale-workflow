import logging

from odoo import api, fields, models
from odoo.fields import Command

logger = logging.getLogger(__name__)

# temporary  warning retro compatibility
WRONG_METHOD = "Current method has been renamed in the file"


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    product_config_ids = fields.One2many(
        comodel_name="product.config",
        string="Product configs",
        inverse_name="order_line_id",
    )

    product_config_id = fields.Many2one(
        comodel_name="product.config",
        string="Product config",
    )

    product_config_id_name = fields.Char(
        related="product_config_id.name", readonly=False, store=True
    )
    product_config_domain = fields.Char()

    is_static_product = fields.Boolean(compute="_compute_is_static_product", store=True)

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)

        for rec in res:
            if rec.product_config_ids and not rec.product_config_id:
                rec._onchange_product_config_ids()
        return res

    def copy_data(self, default=None):
        vals_list = super().copy_data(default)
        for vals in vals_list:
            if "product_config_id" in vals and vals["product_config_id"]:
                product_config_id = vals.pop("product_config_id")
                product_config = self.env["product.config"].browse(product_config_id)
                data = product_config.copy_data()[0]
                vals["product_config_ids"] = [Command.create(data)]
        return vals_list

    @api.depends("product_id", "product_config_id")
    def _compute_is_static_product(self):
        for rec in self:
            rec.is_static_product = not bool(rec.product_config_id)

    def _prepare_default_input_line_vals(self, bom_id):
        logger.warning(f"{WRONG_METHOD} '{__file__}'")
        return self._prepare_default_product_config_vals(bom_id)

    def _prepare_default_product_config_vals(self, bom_id):
        vals = {"bom_id": bom_id.id}
        return vals

    @api.onchange("product_id")
    def onchange_product_template_id(self):
        to_change = {}
        product_config_to_delete = []
        for rec in self:
            template_variable_boms = rec._get_variable_bom()
            if rec.product_config_id and len(template_variable_boms) == 0:
                product_config_to_delete.append(rec.product_config_id.id)
                rec.product_config_ids = [(5, 0, 0)]
                continue

            if rec.product_template_id and len(template_variable_boms) > 0:
                product_config = rec.product_config_id
                if not product_config:
                    if len(template_variable_boms) > 0:
                        rec._create_product_config_from_line(template_variable_boms[0])
                elif product_config.bom_id.product_tmpl_id != rec.product_template_id:
                    to_change[rec.id] = rec.product_config_id.copy_data()[0]
                    product_config_to_delete.append(rec.product_config_id.id)
                    rec.product_config_ids = [(5, 0, 0)]

        for rec in self:
            if rec.id in to_change:
                template_variable_boms = rec._get_variable_bom()
                if len(template_variable_boms) > 0:
                    rec._create_product_config_from_line(
                        template_variable_boms[0], to_change[rec.id]
                    )

    def _get_variable_bom(self):
        template_boms = self.product_template_id.bom_ids
        template_variable_bom = False
        # sale_order_line product_template_id is not static
        # if the product template has a only one bom and that bom
        # is variable
        if (
            len(template_boms) == 1
            and template_boms[0].configuration_type == "variable"
        ):
            template_variable_bom = template_boms[0]
            return [template_variable_bom[0]]

        return []

    def _create_input_line_config_from_line(
        self, template_variable_bom, copy_vals=None
    ):
        self.ensure_one()
        logger.warning(f"{WRONG_METHOD} '{__file__}'")
        return self._create_product_config_from_line(
            template_variable_bom, copy_vals=copy_vals
        )

    def _create_product_config_from_line(self, template_variable_bom, copy_vals=None):
        self.ensure_one()
        # Search if sale_order already has the config_id for this
        # product template
        order_id = (
            self.env["sale.order"].browse(self.order_id.id.origin)
            if getattr(self.order_id.id, "origin", False)
            else self.order_id
        )

        vals = self._prepare_default_product_config_vals(template_variable_bom)

        if copy_vals:
            vals.update(copy_vals)

        product_config = self.env["product.config"].create(vals)
        self.product_config_ids = [(4, product_config.id, 0)]

    @api.onchange("product_config_ids")
    def _onchange_input_line_ids(self):
        logger.warning(f"{WRONG_METHOD} '{__file__}'")
        return self._onchange_product_config_ids()

    @api.onchange("product_config_ids")
    def _onchange_product_config_ids(self):
        for rec in self:
            if len(rec.product_config_ids) > 0:
                rec.product_config_id = rec.product_config_ids[0]
            else:
                rec.product_config_id = False

    def _prepare_procurement_values(self, group_id=False):
        vals = super()._prepare_procurement_values(group_id=group_id)
        if self.lot_id:
            if not self.is_static_product:
                self.lot_id.product_config_id = self.product_config_id.id
            vals["restrict_lot_id"] = self.lot_id.id
        return vals

    def action_show_input_line(self):
        logger.warning(f"{WRONG_METHOD} '{__file__}'")
        return action_show_product_config()

    def action_show_product_config(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Input line information",
            "res_model": "product.config",
            "view_mode": "form",
            "target": "new",
            "res_id": self.product_config_id.id,
        }

    def action_run_copy_data_wizard(self):
        wizard_id = self.env["wizard.copy.product.config.data"].create(
            {
                "product_config_id": self.product_config_id.id,
            }
        )

        return {
            "type": "ir.actions.act_window",
            "name": "Copy product config data",
            "res_model": "wizard.copy.product.config.data",
            "view_mode": "form",
            "target": "new",
            "res_id": wizard_id.id,
        }
