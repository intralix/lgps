# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)

class CheckMarginOnSalesOrder(models.Model):
    _inherit = ['sale.order']

    # @api.model
    # def create(self, vals):
    #     _logger.error('Calling Create Method')
    #     self._check_rules_on_sales_order()
    #     result = super(CheckMarginOnSalesOrder, self).create(vals)
    #     return result

    @api.multi
    def _write(self, values):
        _logger.error('Calling Write Method')
        super(CheckMarginOnSalesOrder, self)._write(values)
        _logger.error('Already Saved. Checking now')
        self._check_rules_on_sales_order()
        return

    # @api.multi
    # def _action_confirm(self):
    #     _logger.error('Calling Create Method')
    #     self._check_rules_on_sales_order()
    #     return super(CheckMarginOnSalesOrder, self)._action_confirm()

    # @api.depends('order_line.margin')
    # def _product_margin(self):
    #     _logger.warning('@api.depends :: order_line.margin')
    #     res =  super(CheckMarginOnSalesOrder, self)._product_margin()
    #
    #     for order in self:
    #         order.internal_margin = sum(order.order_line.filtered(lambda r: r.state != 'cancel').mapped('margin'))
    #         _logger.error('order.internal_margin: %s', order.internal_margin)
    #
    #         # for line in order.order_line:
    #         #     _logger.error('product: %s', line.product_id.name)
    #         #     _logger.error('price_unit: %s', line.price_unit)
    #         #     _logger.error('price_tax: %s', line.price_tax)
    #         #     _logger.error('discount: %s', line.discount)
    #         #     _logger.error('purchase_price: %s', line.purchase_price)
    #         #     _logger.error('price_subtotal: %s', line.price_subtotal)
    #         #     _logger.error('price_total: %s', line.price_total)
    #         #     _logger.error('margin: %s', line.margin)
    #
    #     return res

    def _check_rules_on_sales_order(self):
        # Gettin Max discount Rule
        if self.env.user.max_discount_allowed:
            max_discount_allowed = round(self.env.user.max_discount_allowed * 100)
        else:
            max_discount_allowed = 30

        lower_margin = 1.10
        for order in self:

            amount_untaxed = amount_tax = 0.0
            internal_margin = 0

            _logger.error('Current order %s', order)
            for line in order.order_line:

                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
                line_margin = line.price_subtotal - line.purchase_price
                internal_margin += line_margin
                price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)

                _logger.warning('Line :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::')
                _logger.warning('product: %s', line.product_id.name)
                _logger.warning('quantity: %s', line.product_uom_qty)
                _logger.warning('price_unit: %s', line.price_unit)
                _logger.warning('purchase_price: %s', line.purchase_price)
                _logger.warning('price_tax: %s', line.price_tax)
                _logger.warning('discount: %s', line.discount)
                _logger.warning('price_subtotal: %s', line.price_subtotal)
                _logger.warning('margin: %s', line_margin)
                _logger.warning('price_total: %s', line.price_total)

            amount_total = amount_untaxed + amount_tax
            margin_percent = round(internal_margin / amount_untaxed * 100)
            _logger.error('Base Imponible : %s', amount_untaxed)
            _logger.error('Impuestos : %s', amount_tax)
            _logger.error('Total : %s', amount_total)
            _logger.error('Margin : %s', internal_margin)
            _logger.error('Margin in Percent: %s', margin_percent)
            #_logger.error('amount_untaxed: %s', order.amount_untaxed)

            _logger.error('max_discount_allowed : %s', max_discount_allowed)

            if margin_percent < 0 or margin_percent > max_discount_allowed:
                raise UserError('El margen del presupuesto esta por debajo de lo estipulado.')


class CheckMarginOnSalesOrderLine(models.Model):
    _inherit = ['sale.order.line']

    @api.onchange('price_subtotal')
    def _onchange_price_total(self):
        # _logger.error('api.onchange(price_subtotal) ---------------------------------------------------')
        line = self
        lower_margin = 1.10
        internal_margin = line.purchase_price * lower_margin

        if line.price_subtotal < internal_margin:
            # _logger.error('line: %s', line)
            # _logger.error('product: %s', line.product_id.name)
            # _logger.error('price_unit: %s', line.price_unit)
            # _logger.error('price_tax: %s', line.price_tax)
            # _logger.error('discount: %s', line.discount)
            # _logger.error('purchase_price: %s', line.purchase_price)
            # _logger.error('price_subtotal: %s', line.price_subtotal)
            # _logger.error('price_total: %s', line.price_total)
            # _logger.error('margin: %s', line.margin)
            warning_mess = {
                'title': _('Vendiendo por debajo del costo!'),
                'message': 'Estas intentando vender por debajo del costo interno. \n\nProducto: ' + line.product_id.name
            }
            return {'warning': warning_mess}

        return


class UserMarginConfigurations(models.Model):
    _inherit = ['res.users']

    max_discount_allowed = fields.Float(
        string=_("Max Discount"),
        digits=(2, 2),
        help=_('Max Discount for this users')
    )
