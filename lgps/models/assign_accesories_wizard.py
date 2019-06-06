# -*- coding: utf-8 -*-
from odoo import api, models, fields, _

class AssignAccesoriesWizard(models.TransientModel):
    _name = "lgps.wizard"
    _description = "Add Accesories to Devices"

    def _default_gpsdevices(self):
        return self.env['lgps.gpsdevice'].browse(self._context.get('active_ids'))

    gpsdevice_ids = fields.Many2many(
        comodel_name='lgps.gpsdevice',
        string=_("Gps Device"),
        required=True,
        default=_default_gpsdevices,
    )

    accessory_ids = fields.Many2many(
        comodel_name='lgps.accessory',
        string=_("Accesories")
    )

    @api.multi
    def assign(self):
        for gpsdevice in self.gpsdevice_ids:
            gpsdevice.accessory_ids |= self.accessory_ids

        today = fields.Date.today()
        for accesory in self.accessory_ids:
            accesory.write({'installation_date': today, 'status': 'installed'})
            if accesory.gpsdevice_id.name:
                equipo = accesory.gpsdevice_id.name
            else:
                equipo = "No identificado"

            accesory.message_post(body="Accesorio asignado el día: " + today.strftime('%d-%m-%Y') + " al equipo [<strong>" + equipo + "</strong>]")

        return {}

