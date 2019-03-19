# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from odoo.exceptions import UserError



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

    devices_list = fields.Text(
        string="Devices List"
    )

    cellchips_list = fields.Text(
        string="Cellchips List"
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
                notify_cellchisp_list += '<br/>' + r.cellchip_id.name
                if(r.nick):
                    notify_gps_list += '<br/>' + r.name + ' // ' + r.nick
                else:
                    notify_gps_list += '<br/>' + r.name + ' //  NA'

        self.cellchips_list = notify_cellchisp_list
        self.devices_list = notify_gps_list

        # Alterando las suscripciones
        suscription_close_stage = self.sudo().env.ref('sale_subscription.sale_subscription_stage_closed')
        suscriptions = self.env['sale.subscription'].search([['gpsdevice_id', 'in', active_records.ids]])
        for s in suscriptions:
            s.message_post(body=body)
            s.write({'stage_id': suscription_close_stage.id})

        #cellchips = self.env['lgps.cellchip'].search([['id', 'in', cellchips_ids]])

        channel_msn = '<br/>Los equipos mencionados a continuación se procesaron como baja por motivo de:<br/>'
        channel_msn += self.comment + '<br/>'
        channel_msn += self.devices_list
        channel_msn += '<br/><br/>Se requiere dar de baja la siguientes líneas:<br/>'
        channel_msn += self.cellchips_list

        Config = self.env['ir.config_parameter']
        channel_id = Config.get_param('lgps.drop_device_wizard.default_channel')
        if not channel_id:
           raise UserError(_('There is not configuration for sending email.\n Configure this in order to send the notification.'))
        else:
            poster_bajas = self.sudo().env['mail.channel'].search([('id', '=', channel_id)])
            poster_bajas.message_post(body=channel_msn, subtype='mail.mt_comment', partner_ids=[(4, self.env.uid)])

        return {}
