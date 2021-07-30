# coding: utf-8
# © 2015 Akretion, Valentin CHEMIERE <valentin.chemiere@akretion.com>
# © 2017 David BEAL @ Akretion
# © 2019 Mourad EL HADJ MIMOUNE @ Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, fields, api, models
from odoo.addons import decimal_precision as dp

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    pricelist_id = fields.Many2one(
        related="order_id.pricelist_id", readonly=True)
    option_ids = fields.One2many(
        comodel_name='sale.order.line.option',
        inverse_name='sale_line_id', string='Options', copy=True,
        help="Options can be defined with product bom")
    bom_with_option = fields.Boolean(
        related='product_id.bom_with_option',
        help="Technical: allow conditional options field display",
        store=True)

    @api.multi
    def write(self, vals):
        if vals.get('option_ids'):
            # to fix issue of nesteed many2one we replace [5], [4] option of
            # one2many fileds by [6] option
            # same as : https://github.com/odoo/odoo/issues/17618
            if vals['option_ids'][0][0] == 5:
                ids = []
                for opt_v in vals['option_ids'][1:]:
                    if opt_v[0] == 4:
                        ids.append(opt_v[1])
                vals['option_ids'] = [(6, 0, ids)]
        return super(SaleOrderLine, self).write(vals)

    def _prepare_sale_line_option(self, bline):
        return {
            'bom_line_id': bline.id,
            'product_id': bline.product_id.id,
            'qty': bline.opt_default_qty,
            }

    @api.onchange('product_id')
    def product_id_change(self):
        res = super(SaleOrderLine, self).product_id_change()
        self.option_ids = False
        if self.product_id.bom_with_option:
            options = []
            bom = self.product_id._bom_find()
            for bline in bom.bom_line_ids:
                if bline.opt_default_qty:
                    options.append(
                        (0, 0, self._prepare_sale_line_option(bline)))
            self.option_ids = options
            self.option_ids._compute_price()
            self._onchange_option()
        return res

    @api.onchange('option_ids', 'option_ids.line_price')
    def _onchange_option(self):
        self._compute_price_unit()

    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        res = super(SaleOrderLine, self).product_uom_change()
        if self.product_id.bom_with_option:
            # Odoo play the onchange without specific order
            # we must first be sure to recompute the price
            self.option_ids._compute_price()
            self._onchange_option()
        return res

    @api.model
    def _prepare_vals_lot_number(self, index_lot):
        res = super(SaleOrderLine, self)._prepare_vals_lot_number(index_lot)
        res['option_ids'] = [
            (6, 0, [line.id for line in self.option_ids])
        ]
        return res

    def _compute_price_unit(self):
        if self.product_uom_qty != 0:
            self.price_unit = sum(self.option_ids.mapped('line_price'))/self.product_uom_qty


class SaleOrderLineOption(models.Model):
    _name = 'sale.order.line.option'

    sale_line_id = fields.Many2one(
        comodel_name='sale.order.line',
        required=True,
        ondelete='cascade')
    bom_line_id = fields.Many2one(
        comodel_name='mrp.bom.line',
        string='Bom Line',
        ondelete="set null",
        compute="_compute_bom_line_id",
        store=True)
    product_id = fields.Many2one(
        comodel_name='product.product', string='Product', required=True)
    qty = fields.Float(default=lambda x: x.default_qty)
    min_qty = fields.Float(
        related='bom_line_id.opt_min_qty', readonly=True)
    default_qty = fields.Float(
        related='bom_line_id.opt_default_qty', readonly=True)
    max_qty = fields.Float(
        related='bom_line_id.opt_max_qty', readonly=True)
    invalid_qty = fields.Boolean(
        compute='_compute_invalid_qty', store=True,
        help="Can be used to prevent confirmed sale order")
    line_price_unit = fields.Float(required=True, digits=dp.get_precision('Product Price'), default=0.0)#compute='_compute_price', store=True)
    line_price = fields.Float(compute='_compute_price', store=True)
    product_uom_id = fields.Many2one('uom.uom',
                                     related='bom_line_id.product_uom_id',
                                     readonly=True, store=True)

    _sql_constraints = [
        ('option_unique_per_line',
         'unique(sale_line_id, product_id)',
         'Option must be unique per Sale line. Check option lines'),
    ]

    @api.model
    def create(self, vals):
        res = super(SaleOrderLineOption, self).create(vals)
        return res

    @api.depends('product_id')
    def _compute_bom_line_id(self):
        for record in self:
            bom = record.sale_line_id.product_id._bom_find()
            for line in bom.bom_line_ids:
                if line.product_id == record.product_id:
                    record.bom_line_id = line
                    break

    @api.onchange('product_id')
    def product_id_change(self):
        if self.product_id and self.sale_line_id.pricelist_id:
            self.line_price_unit = self._get_bom_line_price()
        else:
            self.line_price_unit = 0

    @api.onchange('self.bom_line_id.product_uom_id', 'qty')
    def product_uom_change(self):
        if self.product_id and self.sale_line_id.pricelist_id:
            self.line_price_unit = self._get_bom_line_price()
        else:
            self.line_price_unit = 0

    def _get_bom_line_price(self):
        self.ensure_one()
        ctx = {'uom': self.bom_line_id.product_uom_id.id}
        if self.sale_line_id.order_id.date_order:
            ctx['date'] = self.sale_line_id.order_id.date_order
        pricelist = self.sale_line_id.pricelist_id.with_context(ctx)
        price = pricelist.price_get(
            self.product_id.id,
            self.qty * self.sale_line_id.product_uom_qty,
            self.sale_line_id.order_id.partner_id.id)
        return price[pricelist.id]

    @api.depends('qty', 'product_id', 'sale_line_id.product_uom_qty')
    def _compute_price(self):
        for record in self:
            if record.product_id and record.sale_line_id.pricelist_id:
                if not record.line_price_unit:
                    record.line_price_unit = record._get_bom_line_price()
                record.line_price = record.line_price_unit * record.qty
            else:
                record.line_price_unit = 0
                record.line_price = 0
            record.sale_line_id._compute_price_unit()

    def _is_quantity_valid(self, record):
        """Ensure product_uom_qty <= qty <= max_qty."""
        # La notion de min max doit être revue car ne correspond
        # pas au produits sur mesure (atoutcofrage)
        # if not record.bom_line_id:
            # return True
        # if record.qty < record.bom_line_id.opt_min_qty:
            # return False
        # if record.qty > record.bom_line_id.opt_max_qty:
            # return False
        return True

    @api.depends('qty')
    def _compute_invalid_qty(self):
        for record in self:
            record.invalid_qty = not record._is_quantity_valid(record)

    @api.onchange('qty')
    def onchange_qty(self):
        for record in self:
            if record.invalid_qty:
                return {'warning': {
                    'title': _('Error on quantity'),
                    'message': _(
                        "The quantity is not between the max and the min"
                        )
                    }
                    }
            record._compute_price()

    @api.onchange('line_price_unit')
    def onchange_line_price_unit(self):
        self._compute_price()
