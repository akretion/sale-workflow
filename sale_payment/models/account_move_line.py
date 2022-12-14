# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    # a payment can be linked to one sale order only. We could change this field
    # to a many2many but then we should find a way to manage the amount
    # repartition between the sale orders
    sale_id = fields.Many2one(
        comodel_name="sale.order",
        string="Sales Orders",
        compute="_compute_sale_id",
        store=True,
        readonly=False,
    )

    @api.constrains("sale_id", "account_id")
    def sale_id_check(self):
        for line in self:
            if line.sale_id and line.account_id.account_type != "asset_receivable":
                raise ValidationError(
                    _(
                        "The account move line '%(line_name)s' is linked to sale order"
                        " '%(order_name)s' but it uses account '%(account_name)s' which"
                        " is not a receivable account."
                    )
                    % {
                        "line_name": line.name,
                        "order_name": line.sale_id.name,
                        "account_name": line.account_id.display_name,
                    }
                )

    @api.depends("account_id")
    def _compute_sale_id(self):
        for aml in self.filtered(
            lambda line: line.sale_id
            and line.account_id.account_type != "asset_receivable"
        ):
            aml.sale_id = False
