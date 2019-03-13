# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
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
        if len(self._context.get('active_ids')) < 1:
            raise UserError(_('Select at least one record.'))
        if not self.comment:
            raise UserError(_('You forgot to comment the reason for this process to run.'))

        active_model = self._context.get('active_model')
        active_records = self.env[active_model].browse(self._context.get('active_ids'))

        active_records.write({'platform': "Drop"})
        body = "Proceso de Baja: <br><br>" + self.comment
        cellchips_ids = []
        notify_cellchisp_list = ""
        notify_gps_list = ""

        for r in active_records:
            r.message_post(body=body)
            if(r.cellchip_id):
                cellchips_ids.append(r.cellchip_id.id)
                notify_gps_list += '<br>' + r.name + ' // ' + r.nick
                notify_cellchisp_list += '<br>' + r.cellchip_id.name


        #suscriptions = self.env['sale.subscription'].search([['gpsdevice_id', 'in', active_records.ids]])
        #cellchips = self.env['lgps.cellchip'].search([['id', 'in', cellchips_ids]])

        channel_msn = '<br>Los equipos mencionados a continuación se procesaron como baja:<br>'
        channel_msn += '<strong>' + notify_gps_list + '</strong>'
        channel_msn += '<br><br>Se requiere dar de baja la siguientes líneas:<br>'
        channel_msn += '<strong>' + notify_cellchisp_list + '</strong>'

        poster = self.sudo().env.ref('mail.channel_all_employees')
        poster.message_post(body=channel_msn, subtype='mail.mt_comment', partner_ids=[self.env.uid])

        mail = self.env['mail.thread']
        mail.message_post(
           type="notification",
           subtype="mail.mt_comment",
           partner_ids=[self.env.uid],
           author_id=self.env.uid,
           subject="Baja de Equipos",
           body=body
        )

        mail_details = {
            'subject': "Baja de Equipos",
            'body': body,
            'partner_ids': [self.env.uid],
            'author_id': self.env.uid,
        }
        mail = self.env['mail.thread']
        mail.message_post(type="notification", subtype="mail.mt_comment", **mail_details)

        return {}