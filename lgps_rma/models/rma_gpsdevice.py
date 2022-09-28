# -*- coding: utf-8 -*-

from odoo import api, models, fields, _
import logging

_logger = logging.getLogger(__name__)


class RmaGpsDevice(models.Model):
    _inherit = 'lgps.gpsdevice'

    rma_ids = fields.One2many(
        comodel_name="lgps.rma_process",
        inverse_name="gpsdevice_id",
        string=_("RMAs"),
    )

    rma_count = fields.Integer(
        string=_('RMA Count'),
        compute='_compute_rma_count',
    )

    @api.multi
    def _compute_rma_count(self):
        for rec in self:
            rec.rma_count = self.env['lgps.rma_process'].search_count([('gpsdevice_id', '=', rec.id)])
            _logger.error(" State : %s", rec.rma_count)
