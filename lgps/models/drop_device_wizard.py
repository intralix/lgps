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

    requeste_by = fields.Char(
        string=_("Requested by"),
        required=True,
    )

    comment = fields.Text(
        string=_("Drop Reason"),
        required=True,
    )

    devices_list = fields.Text(
        string=_("Devices List")
    )

    cellchips_list = fields.Text(
        string=_("Cellchips List")
    )

    @api.multi
    def execute_drop(self):
        if len(self._context.get('active_ids')) < 1:
            raise UserError(_('Select at least one record.'))
        if not self.comment:
            raise UserError(_('You forgot to comment the reason for this process to run.'))

        # Obtenemos los Ids seleccionados
        active_model = self._context.get('active_model')
        active_records = self.env[active_model].browse(self._context.get('active_ids'))

        # Buffer Vars
        cellchips_ids = []
        notify_cellchisp_list = ""
        notify_gps_list = ""
        requested_by = self.requeste_by

        # Procesamos los quipos seleccionados:
        for r in active_records:
            body = "[Proceso de Baja]<br/><br/>" + self.comment + '<br/>'
            gps_functions_summary = "<hr/>Se desactivaron las funciones de:<br/><br/>"
            acumulador = ""
            aditional_functions = False

            platform = r.platform if r.platform else 'Sin Plataforma'
            chip = r.cellchip_id.name if r.cellchip_id else 'Sin chip'
            pchip = r.cellchip_id.provider if r.cellchip_id else 'Sin chip'
            client = r.client_id.name if r.client_id else 'Sin Cliente'
            equipo = r.name
            nick = r.nick if r.nick else 'NA'

            acumulador += '<br/><b>Plataforma:</b> ' + platform
            acumulador += '<br/><b>Cliente:</b> ' + client
            acumulador += '<br/><b>Solicitado Por:</b> ' + requested_by
            acumulador += '<br/><b>Equipo:</b> ' + equipo
            acumulador += '<br/><b>Nick:</b> ' + nick
            acumulador += '<br/><b>Línea:</b> ' + chip
            acumulador += '<br/><b>Prov. Linea:</b> ' + pchip

            if(r.cellchip_id):
                cellchips_ids.append(r.cellchip_id.id)
                notify_cellchisp_list += '<br/>' + r.cellchip_id.name + ' - ' + r.cellchip_id.provider

            notify_gps_list += '<br/>' + client + ' || ' + equipo + ' || ' + nick + ' || ' + platform

            # Comprobando funciones adicionales
            if r.tracking:
                aditional_functions = True
                gps_functions_summary += "Rastreo<br/>"
            if r.fuel:
                aditional_functions = True
                gps_functions_summary += "Combustible<br/>"
            if r.scanner:
                aditional_functions = True
                gps_functions_summary += "Escánner<br/>"
            if r.temperature:
                aditional_functions = True
                gps_functions_summary += "Temperatura<br/>"
            if r.logistic:
                aditional_functions = True
                gps_functions_summary += "Logística<br/>"

            body += '<br/>' + acumulador
            if aditional_functions:
                body += gps_functions_summary
            r.message_post(body=body)

        # Ejecutamos la Baja en el sistema
        active_records.write({
            'tracking': False,
            'fuel': False,
            'scanner': False,
            'temperature': False,
            'logistic': False,
            'platform': "Drop",
        })

        self.cellchips_list = notify_cellchisp_list
        self.devices_list = notify_gps_list

        # Alterando las suscripciones
        suscription_close_stage = self.sudo().env.ref('sale_subscription.sale_subscription_stage_closed')
        suscriptions = self.env['sale.subscription'].search([['gpsdevice_id', 'in', active_records.ids]])
        for s in suscriptions:
            s.message_post(body="El equipo se ha dado de baja en el sistema.")
        suscriptions.write({'stage_id': suscription_close_stage.id})

        #cellchips = self.env['lgps.cellchip'].search([['id', 'in', cellchips_ids]])

        channel_msn = '<br/>Los equipos mencionados a continuación se procesaron para dar de baja por motivo de:<br/>'
        channel_msn += self.comment + '<br/>'
        channel_msn += self.devices_list
        channel_msn += '<br/><br/>Se requiere dar de baja la siguientes líneas:<br/>'
        channel_msn += self.cellchips_list

        Config = self.sudo().env['ir.config_parameter']
        channel_id = Config.get_param('lgps.drop_device_wizard.default_channel')
        if not channel_id:
           raise UserError(_('There is not configuration for default channel.\n Configure this in order to send the notification.'))
        else:
            poster_bajas = self.sudo().env['mail.channel'].search([('id', '=', channel_id)])
            poster_bajas.message_post(body=channel_msn, subtype='mail.mt_comment', partner_ids=[(4, self.env.uid)])

        return {}
