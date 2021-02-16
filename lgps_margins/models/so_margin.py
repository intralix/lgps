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

    @api.depends('margin', 'amount_untaxed')
    def _compute_margin_percent(self):
        for record in self:
            if not (record.margin and record.amount_untaxed):
                record.margin_percent = 0
            else:
                # _logger.warning('margin: %s', record.margin)
                # _logger.warning('amount_untaxed: %s', record.amount_untaxed)
                record.margin_percent = ((record.margin * 100) / record.amount_untaxed / 100)
                # _logger.error('margin_percent afther all: %s', record.margin_percent)



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
        # _logger.info('Trabajando con el usuario : %s', self.env.user)
        max_discount_allowed = user.min_margin * 100
        # _logger.info('Max discount allowed : %s', max_discount_allowed)
        margin_percent = self.margin_percent * 100
        # _logger.info('Sel Margin Discount: %s', margin_percent)

        _logger.info(':::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::')
        _logger.info('Base Imponible : %s', self.amount_untaxed)
        _logger.info('Impuestos : %s', self.amount_tax)
        _logger.info('Total : %s', self.amount_total)
        _logger.info('Margin : %s', self.margin)
        _logger.info('Margin in decimal: %s', self.margin_percent)
        _logger.info('Margin in Percent: %s', margin_percent)

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
