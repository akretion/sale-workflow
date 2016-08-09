# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Florian da Costa
#    Copyright 2016 Akretion
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import models, fields, api


class AccountBankStatementLine(models.Model):
    _inherit = 'account.bank.statement.line'

    sale_ids = fields.Many2many(
        comodel_name='sale.order',
        string='Sales Orders')

    def process_reconciliation(self, counterpart_aml_dicts=None,
                               payment_aml_rec=None, new_aml_dicts=None):
        if new_aml_dicts and self.sale_ids:
            for aml_dict in new_aml_dicts:
                aml_dict['sale_ids'] = [(6, 0, self.sale_ids.ids)]
        return super(AccountBankStatementLine, self).process_reconciliation(
            counterpart_aml_dicts=counterpart_aml_dicts,
            payment_aml_rec=payment_aml_rec, new_aml_dicts=new_aml_dicts)

    @api.onchange('sale_ids')
    def onchange_sale_ids(self):
        if self.sale_ids:
            self.partner_id = self.sale_ids[0].partner_id.id
            self.account_id = self.partner_id.\
                              property_account_receivable_id.id
