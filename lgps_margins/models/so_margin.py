# -*- coding: utf-8 -*-

from odoo import api, models, fields, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)


class CheckMarginOnSalesOrder(models.Model):
    _inherit = ['sale.order']

    margin_percent = fields.Float(
        string=_("Margin Percent"),
        digits=(12, 2),
        compute='_compute_margin_percent',
        store=True,
    )

    sacrifice_sale = fields.Boolean(
        string=_("Sell at a loss"),
        default=False,
        help=_('Allow to Sell at a loss')
    )

    @api.one
    @api.depends('margin', 'amount_untaxed')
    def _compute_margin_percent(self):
        if not (self.margin and self.amount_untaxed):
            self.margin_percent = 0
        else:
            self.margin_percent = (self.margin / self.amount_untaxed)

    @api.model
    def create(self, values):
        _logger.warning('Calling Created Method')
        _logger.warning('%s', self)
        new_record = super(CheckMarginOnSalesOrder, self).create(values)
        new_record.check_rules_on_sales_order()
        return new_record

    @api.multi
    def write(self, values):
        _logger.warning('Calling Write Method')
        _logger.warning('%s', self)

        for po in self:
            _logger.info('Running for PO %s', po.id)
            po.check_rules_on_sales_order()

        return super(CheckMarginOnSalesOrder, self).write(values)

    def check_rules_on_sales_order(self):
        # Gettin Max discount Rule
        user = self.env.user
        _logger.info('Trabajando con el usuario : %s', self.env.user)
        max_discount_allowed = round(user.min_margin * 100)
        _logger.info('Max discount allowed : %s', max_discount_allowed)

        order = self
        amount_untaxed = amount_tax = 0.0
        internal_margin = 0

        _logger.info('Current order %s', order)
        for line in order.order_line:

            amount_untaxed += line.price_subtotal
            amount_tax += line.price_tax
            line_margin = line.price_subtotal - line.purchase_price
            internal_margin += line_margin
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)

            _logger.info('Line :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::')
            _logger.info('product: %s', line.product_id.name)
            _logger.info('quantity: %s', line.product_uom_qty)
            _logger.info('price_unit: %s', line.price_unit)
            _logger.info('purchase_price: %s', line.purchase_price)
            _logger.info('price_tax: %s', line.price_tax)
            _logger.info('discount: %s', line.discount)
            _logger.info('price_subtotal: %s', line.price_subtotal)
            _logger.info('margin: %s', line_margin)
            _logger.info('price_total: %s', line.price_total)

        amount_total = amount_untaxed + amount_tax
        if amount_untaxed > 0:
            margin_percent = round(internal_margin / amount_untaxed * 100)
        else:
            margin_percent = 0

        _logger.info(':::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::')
        _logger.info('Base Imponible : %s', amount_untaxed)
        _logger.info('Impuestos : %s', amount_tax)
        _logger.info('Total : %s', amount_total)
        _logger.info('Margin : %s', internal_margin)
        _logger.info('Margin in Percent: %s', margin_percent)
        _logger.info('amount_untaxed: %s', order.amount_untaxed)

        if margin_percent < 0 or margin_percent < max_discount_allowed:
            if user.skip_min_margin_rule is False:
                raise UserError('El margen del presupuesto esta por debajo de lo esperado.')
            else:
                self.message_post(body='El usuario cuenta con permisos para vender con pérdida.')

        return


class CheckMarginOnSalesOrderLine(models.Model):
    _inherit = ['sale.order.line']

    @api.onchange('price_subtotal')
    def _onchange_price_total(self):
        line = self
        lower_margin = 1.10
        internal_margin = line.purchase_price * lower_margin
        _logger.warning('Precio del Producto : %s', line.purchase_price)
        _logger.warning('Precio Minimo de Venta: %s', internal_margin)
        _logger.warning('Subtotal: %s', line.price_subtotal)

        if line.price_subtotal < internal_margin:
            product_description = line.product_id.default_code + ' - ' + line.product_id.name
            warning_mess = {
                'title': _('Vendiendo por debajo del costo!'),
                'message': 'Estas intentando vender por debajo del costo interno. \n\nProducto: ' + product_description
            }
            return {'warning': warning_mess}
