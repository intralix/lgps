# -*- coding: utf-8 -*-
from odoo import api, models, fields
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)


class DropDeviceWizard(models.TransientModel):
    _name = "lgps.drop_device_wizard"
    _description = "Drop Device Wizard"

    def _default_gpsdevices(self):
        return self.env['lgps.gpsdevice'].browse(self._context.get('active_ids'))

    gpsdevice_ids = fields.Many2many(
        comodel_name='lgps.gpsdevice',
        string="Gps Device",
        required=True,
        default=_default_gpsdevices,
    )

    comment = fields.Text(
        string="Drop Reason"
    )

    @api.multi
    def execute_drop(self):
        active_model = self._context.get('active_model')
        active_records = self.env[active_model].browse(self._context.get('active_ids'))
        _logger.warning('Comment %s', self.comment)
        _logger.warning('Create a %s with vals %s', active_model, active_records)
        if active_model == 'lgps.gpsdevice':
            for r in active_records:
                _logger.warning('Device [%s] with nick [%s]', r.name, r.nick)
                r.write({'platform': "Drop"})
                body = "BAJA <br>"+self.comment
                r.message_post(body=body)
                #user_id = self.user_target.id
                _logger.warning('User ID [%s]', self._uid)
                mail_details = {'subject': "Baja de Equipos",
                                'body': body,
                                'user_ids': [self._uid]
                                }
                mail = self.env['mail.thread']
                mail.message_post(type="notification", subtype="mail.mt_comment", **mail_details)


