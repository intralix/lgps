# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)


class CheckMargin(models.Model):
    _name = 'sale.order'
    _inherit = ['sale.order']

    bad_cost = fields.Float(compute='_product_cost_ok')

    @api.depends('order_line.price_unit')
    def _product_cost_ok(self):
        for order in self:
            order.bad_cost = sum(order.order_line.filtered(lambda r: r.state != 'cancel').mapped('margin'))

    @api.multi
    def _action_confirm(self):

        lower_margin = 1.10
        internal_margin = 0

        for line in self.order_line:

            internal_margin = line.purchase_price * lower_margin

            if line.price_subtotal < internal_margin:
                raise UserError('Estas intentando vender por debajo del costo interno. \n\nProducto: ' + line.product_id.name)

            _logger.error('line: %s', line)
            _logger.error('line: %s', line.price_unit)
            _logger.error('line: %s', line.price_tax)
            _logger.error('order.bad_cost: %s', self.bad_cost)

        if self.margin < 0:
            raise UserError('El margen del presupuesto esta por debajo de lo estipulado.')

        return super(CheckMargin, self)._action_confirm()
