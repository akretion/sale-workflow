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
from openerp.exceptions import Warning


class SaleOrder(models.Model):
    _inherit = 'sale.order.line'

    payment_ids = fields.Many2many(
        comodel_name='account.move.line',
        string='Payments Entries',
        domain=[('account_id.type', '=', 'receivable')],
        copy=False,
    )
