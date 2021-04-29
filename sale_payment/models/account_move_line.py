# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    # a payment can be linked to one sale order only. We could change this field
    # to a many2many but then we should find a way to manage the amount
    # repartition between the sale orders
    sale_id = fields.Many2one(comodel_name="sale.order", string="Sales Orders")

    @api.constrains("sale_id", "account_id")
    def sale_id_check(self):
        for line in self:
            if line.sale_id and line.account_id.internal_type != "receivable":
                raise ValidationError(
                    _(
                        "The account move line '%s' is linked to sale order '%s' "
                        "but it uses account '%s' which is not a receivable "
                        "account."
                    )
                    % (
                        line.name,
                        line.sale_id.name,
                        line.account_id.display_name,
                    )
                )

    @api.onchange("account_id")
    def sale_advance_payement_account_id_change(self):
        if self.sale_id and self.account_id.user_type_id.type != "receivable":
            self.sale_id = False
