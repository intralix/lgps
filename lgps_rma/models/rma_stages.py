# -*- coding: utf-8 -*-

from odoo import api, models, fields, _
import logging

_logger = logging.getLogger(__name__)


class RmaProcessStage(models.Model):
    _name = 'lgps.rma.process.stage'
    _description = 'Rma Process Stage'
    _order = 'sequence,name'

    name = fields.Char()
    sequence = fields.Integer(default=10)
    fold = fields.Boolean()
    active = fields.Boolean(default=True)
    state = fields.Selection([
        ('reception', _('Reception')),
        ('shipment_to_supplier', _('Shipment to Supplier')),
        ('delivery_to_customer', _('Delivery to Customer')),
        ('done', _('Done'))
    ], defatul='reception')
