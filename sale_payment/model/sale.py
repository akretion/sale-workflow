# -*- coding: utf-8 -*-
#########################################################################
#  Copyright (C) 2011 Akretion (Sébastien BEAU)                         #
#  Copyright 2013 Camptocamp SA (Guewen Baconnier)                      #
#  Copyright (C) 2016  Akretion                                          #
#                                                                       #
# This program is free software: you can redistribute it and/or modify  #
# it under the terms of the GNU Affero General Public License as        #
# published by the Free Software Foundation, either version 3 of the    #
# License, or (at your option) any later version.                       #
#                                                                       #
# This program is distributed in the hope that it will be useful,       #
# but WITHOUT ANY WARRANTY; without even the implied warranty of        #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         #
# GNU Affero General Public Licensefor more details.                    #
#                                                                       #
# You should have received a copy of the                                #
# GNU Affero General Public License                                     #
# along with this program.  If not, see <http://www.gnu.org/licenses/>. #
#                                                                       #
#########################################################################

from openerp import fields, models, api, _
import openerp.addons.decimal_precision as dp


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.one
    def _get_residual(self):
        total = 0.0
        paid_amount = 0.0
        for line in self.payment_ids:
            amount = line.credit - line.debit
            if line.currency_id != self.currency_id:
                from_currency = (line.currency_id and \
                                 line.currency_id.with_context(
                                    date=line.date)) or \
                                 line.company_id.currency_id.with_context(
                                    date=line.date)
                amount = from_currency.compute(amount, self.currency_id)
            paid_amount += amount
        self.residual = self.amount_total - paid_amount
        self.amount_paid = paid_amount
            

    payment_ids = fields.Many2many(
        comodel_name='account.move.line',
        string='Payments Entries',
        domain=[('account_id.internal_type', '=', 'receivable')],
        copy=False,
    )
    residual = fields.Float(
        compute='_get_residual',
        digits_compute=dp.get_precision('Account'))
    amount_paid = fields.Float(
        compute='_get_residual',
        digits_compute=dp.get_precision('Account'))
