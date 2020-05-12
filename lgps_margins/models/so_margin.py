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

    @api.one
    @api.depends('margin', 'amount_untaxed')
    def _compute_margin_percent(self):
        if not (self.margin and self.amount_untaxed):
            self.margin_percent = 0
        else:
            self.margin_percent = (self.margin / self.amount_untaxed)

    @api.multi
    def _write(self, values):
        # _logger.error('Calling Write Method')
        for po in self:
            po._check_rules_on_sales_order()
        # _logger.error('Already Saved. Checking now')
        return super(CheckMarginOnSalesOrder, self)._write(values)

    def _check_rules_on_sales_order(self):

        # Gettin Max discount Rule
        user = self.env.user
        _logger.error('Trabajando con el usuario : %s', self.env.user)
        if user.id == 1:
            if self.user_id:
                user = self.env['res.users'].search([['id', '=', self.user_id.id]], limit=1)
                _logger.error('Cambiando a el usuario : %s', user)

        max_discount_allowed = round(user.min_margin * 100)
        skip_min_margin_rule = user.skip_min_margin_rule
        lower_margin = 1.10

        _logger.error('self : %s', self)
        # _logger.error('self.env.uid : %s', self.env.uid)
        # _logger.error('self.env.user.name : %s', user.name)
        # _logger.error('self.env.user.email : %s', user.email)
        # _logger.error('self.env.user.company_id.id : %s', user.company_id.id)
        _logger.error('max_discount_allowed : %s', max_discount_allowed)
        _logger.error('skip_min_margin_rule : %s', skip_min_margin_rule)
        #_logger.error('vendedor : %s', self.user_id)
        # raise UserError('Excepcón controlada para ver variables')
        # _logger.warning('===============================================')
        order = self
        amount_untaxed = amount_tax = 0.0
        internal_margin = 0

        _logger.error('Current order %s', order)
        for line in order.order_line:

            amount_untaxed += line.price_subtotal
            amount_tax += line.price_tax
            line_margin = line.price_subtotal - line.purchase_price
            internal_margin += line_margin
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)

            # _logger.warning('Line :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::')
            # _logger.warning('product: %s', line.product_id.name)
            # _logger.warning('quantity: %s', line.product_uom_qty)
            # _logger.warning('price_unit: %s', line.price_unit)
            # _logger.warning('purchase_price: %s', line.purchase_price)
            # _logger.warning('price_tax: %s', line.price_tax)
            # _logger.warning('discount: %s', line.discount)
            # _logger.warning('price_subtotal: %s', line.price_subtotal)
            # _logger.warning('margin: %s', line_margin)
            # _logger.warning('price_total: %s', line.price_total)

        amount_total = amount_untaxed + amount_tax
        if amount_untaxed > 0:
            margin_percent = round(internal_margin / amount_untaxed * 100)
        else:
            margin_percent = 0
            
        _logger.error('Base Imponible : %s', amount_untaxed)
        _logger.error('Impuestos : %s', amount_tax)
        _logger.error('Total : %s', amount_total)
        _logger.error('Margin : %s', internal_margin)
        _logger.error('Margin in Percent: %s', margin_percent)
        _logger.error('amount_untaxed: %s', order.amount_untaxed)

        if skip_min_margin_rule:
            return
            # _logger.warning('Evitando la regla del MArgen')
            # if margin_percent <= 0:
            #     _logger.warning('Margen Negativo, Intentando notificar')
            #     warning_mess = {
            #          'title': _('Vendiendo con pérdida'),
            #          'message': 'Esta venta se está realizando con pérdida'
            #     }
            #     return {'warning': warning_mess}
        elif margin_percent < 0 or margin_percent < max_discount_allowed:
            raise UserError('El margen del presupuesto esta por debajo de lo esperado.')

        return

class CheckMarginOnSalesOrderLine(models.Model):
    _inherit = ['sale.order.line']

    @api.onchange('price_subtotal')
    def _onchange_price_total(self):
        line = self
        lower_margin = 1.10
        internal_margin = line.purchase_price * lower_margin

        if line.price_subtotal < internal_margin:
            warning_mess = {
                'title': _('Vendiendo por debajo del costo!'),
                'message': 'Estas intentando vender por debajo del costo interno. \n\nProducto: ' + line.product_id.name
            }
            return {'warning': warning_mess}

        return
