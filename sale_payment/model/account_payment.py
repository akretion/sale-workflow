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


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    sale_id = fields.Many2one(
        'sale.order',
        string='Sales Order')

    @api.model
    def default_get(self, fields):
        rec = super(AccountPayment, self).default_get(fields)
        if not self.env.context.get('active_model') == 'sale.order':
            return rec
        sale_id = self.env.context.get('active_id')
        sale = self.env['sale.order'].browse(sale_id)

        rec['communication'] = sale.name
        rec['currency_id'] = sale.currency_id.id
        rec['payment_type'] = 'inbound'
        rec['partner_type'] = 'customer'
        rec['partner_id'] = sale.partner_invoice_id.id
        rec['amount'] = sale.residual
        rec['sale_id'] = sale.id
        return rec

    def _get_counterpart_move_line_vals(self, invoice=False):
        res = super(AccountPayment, self)._get_counterpart_move_line_vals(
            invoice=invoice)
        sale_ids = []
        if invoice:
            for inv in invoice:
                for invoice_line in invoice.invoice_line_ids:
                    sale_ids += [
                        sl.order_id.id for sl in invoice_line.sale_line_ids \
                        if sl.order_id.id not in sale_ids]
        elif self.sale_id:
            sale_ids.append(self.sale_id.id)
        res['sale_ids'] = [(6, 0, sale_ids)]
        return res
