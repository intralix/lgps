# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class CheckMarginOnSalesOrder(models.Model):
    _inherit = ['sale.order']

    @api.model
    def create(self, vals):
        _logger.error('Calling Create Method')
        #self._check_rules_on_sales_order()
        result = super(CheckMarginOnSalesOrder, self).create(vals)
        return result

    @api.multi
    def _write(self, values):
        _logger.error('Calling Write Method')
        #self._check_rules_on_sales_order()
        return super(CheckMarginOnSalesOrder, self)._write(values)

    @api.multi
    def _action_confirm(self):
        _logger.error('Calling Create Method')
        #self._check_rules_on_sales_order()
        return super(CheckMarginOnSalesOrder, self)._action_confirm()

    def _check_rules_on_sales_order(self):
        lower_margin = 1.10
        internal_margin = 0
        for order in self:
            for line in order.order_line:
                internal_margin = line.purchase_price * lower_margin

                if line.price_subtotal < internal_margin:
                    _logger.error('line: %s', line)
                    _logger.error('internal_margin: %s', internal_margin)
                    _logger.error('product: %s', line.product_id.name)
                    _logger.error('price_unit: %s', line.price_unit)
                    _logger.error('price_tax: %s', line.price_tax)
                    _logger.error('discount: %s', line.discount)
                    _logger.error('purchase_price: %s', line.purchase_price)
                    _logger.error('price_subtotal: %s', line.price_subtotal)
                    _logger.error('price_total: %s', line.price_total)
                    _logger.error('margin: %s', line.margin)

                    raise UserError(
                        'Estas intentando vender por debajo del costo interno. \n\nProducto: ' + line.product_id.name)

            if self.margin < 0:
                raise UserError('El margen del presupuesto esta por debajo de lo estipulado.')


class CheckMarginOnSalesOrderLine(models.Model):
    _inherit = ['sale.order.line']

    @api.onchange('price_subtotal')
    def _onchange_price_total(self):
        self._check_rules_on_sales_order()

    def _check_rules_on_sales_order(self):
        line = self

        lower_margin = 1.10
        internal_margin = line.purchase_price * lower_margin

        if line.price_subtotal < internal_margin:
            _logger.error('line: %s', line)
            _logger.error('product: %s', line.product_id.name)
            _logger.error('price_unit: %s', line.price_unit)
            _logger.error('price_tax: %s', line.price_tax)
            _logger.error('discount: %s', line.discount)
            _logger.error('purchase_price: %s', line.purchase_price)
            _logger.error('price_subtotal: %s', line.price_subtotal)
            _logger.error('price_total: %s', line.price_total)
            _logger.error('margin: %s', line.margin)

            raise UserError('Estas intentando vender por debajo del costo interno. \n\nProducto: '
                            + line.product_id.name)
