# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    discount_total = fields.Float(
        compute='_compute_discount',
        string='Discount Subtotal',
        readonly=True,
        store=True)
    price_total_no_discount = fields.Float(
        compute='_compute_discount',
        string='Subtotal Without Discount',
        readonly=True,
        store=True)

    @api.depends('order_line.discount_total', 'order_line.discount_total')
    def _compute_discount(self):
        for order in self:
            discount_total = sum(order.order_line.mapped('discount_total'))
            price_total_no_discount = sum(
                order.order_line.mapped('price_total_no_discount'))
            order.update({
                'discount_total': discount_total,
                'price_total_no_discount': price_total_no_discount
            })
