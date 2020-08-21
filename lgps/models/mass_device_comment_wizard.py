# -*- coding: utf-8 -*-
from datetime import timedelta
from odoo import api, models, fields, _
from odoo.exceptions import UserError
import logging

class MassDeviceCommentWizard(models.TransientModel):
    _name = "lgps.mass_device_comment_wizard"
    _description = "Mass Comments To Devices Wizard"

    def _default_gpsdevices(self):
        return self.env['lgps.gpsdevice'].browse(self._context.get('active_ids'))

    gpsdevice_ids = fields.Many2many(
        comodel_name='lgps.gpsdevice',
        string="Gps Device",
        required=True,
        default=_default_gpsdevices,
    )

    comment = fields.Text(
        string=_("Comment"),
        required=True,
    )

    @api.multi
    def execute_operation(self):
        active_model = self._context.get('active_model')
        active_records = self.env[active_model].browse(self._context.get('active_ids'))
        for r in active_records:
            body = self.comment
            r.message_post(body=body)

        return {}
