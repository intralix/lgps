# -*- coding: utf-8 -*-
from odoo import api, models, fields
#Sesion = GPS /
class Wizard(models.TransientModel):
    _name = "lgps.wizard"

    def _default_gpsdevices(self):
        return self.env['lgps.gpsdevice'].browse(self._context.get('active_ids'))

    gpsdevice_ids = fields.Many2many(
        comodel_name='lgps.gpsdevice',
        string="Gps Device",
        required=True,
        default=_default_gpsdevices,
    )

    accessory_ids = fields.Many2many(
        comodel_name='lgps.accessory',
        string="Accesories"
    )

    @api.multi
    def assign(self):
        for gpsdevice in self.gpsdevice_ids:
            gpsdevice.accessory_ids |= self.accessory_ids
        return {}
