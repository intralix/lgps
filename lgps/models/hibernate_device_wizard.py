# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from odoo.exceptions import UserError
from datetime import timedelta
import logging
_logger = logging.getLogger(__name__)

class HibernateDeviceWizard(models.TransientModel):
    _name = "lgps.hibernate_device_wizard"
    _description = "Hibernate Device Wizard"

    def _default_gpsdevices(self):
        return self.env['lgps.gpsdevice'].browse(self._context.get('active_ids'))

    gpsdevice_ids = fields.Many2many(
        comodel_name='lgps.gpsdevice',
        string="Gps Device",
        required=True,
        default=_default_gpsdevices,
    )

    comment = fields.Text(
        string=_("Hibernate Reason"),
        required=True,
    )

    devices_list = fields.Text(
        string="Devices List"
    )

    requeste_by = fields.Char(
        string=_("Requested by"),
        required=True,
    )

    @api.multi
    def execute_hibernation(self):
        if len(self._context.get('active_ids')) < 1:
            raise UserError(_('Select at least one record.'))
        if not self.comment:
            raise UserError(_('You forgot to comment the reason for this process to run.'))
        if not self.requeste_by:
            raise UserError(_('Who authorizes this request?'))

        # LGPS Global Configuration
        LgpsConfig = self.sudo().env['ir.config_parameter']

        suscription_hibernate_stage_id = LgpsConfig.get_param(
            'lgps.hibernate_device_wizard.default_subscription_stage')
        if not suscription_hibernate_stage_id:
            raise UserError(_(
                'There is not configuration for default channel.\n Configure this in order to send the notification.'))

        suscription_hibernate_template_id = LgpsConfig.get_param(
            'lgps.hibernate_device_wizard.default_subscription_template')
        if not suscription_hibernate_template_id:
            raise UserError(_(
                'There is not configuration for default channel.\n Configure this in order to send the notification.'))

        channel_id = LgpsConfig.get_param('lgps.hibernate_device_wizard.default_channel')
        if not channel_id:
            raise UserError(_(
                'There is not configuration for default channel.\n Configure this in order to send the notification.'))

        # Obtenemos los Ids seleccionados
        active_model = self._context.get('active_model')
        active_records = self.env[active_model].browse(self._context.get('active_ids'))
        # Subscriptions Config vars
        #subscription_close_stage = self.sudo().env.ref('sale_subscription.sale_subscription_stage_upsell').ensure_one()
        #subscription_hibernation_stage = self.sudo().env.ref('sale_subscription.sale_subscription_stage_upsell').ensure_one()

        # Buffer Vars
        notify_gps_list = ""
        skip_subscription_ids = []

        # Procesamos los quipos seleccionados:
        for r in active_records:
            body = "[Proceso de Hibernación]<br/><br/>" + self.comment + '<br/><b>Solicitado por</b>: ' + self.requeste_by + '<br/>'
            gps_functions_summary = "<hr/>Se desactivaron las funciones de:<br/><br/>"
            acumulador = ""
            aditional_functions = False

            platform = r.platform if r.platform else 'Sin Plataforma'
            chip = r.cellchip_id.name if r.cellchip_id else 'Sin chip'
            client = r.client_id.name if r.client_id else 'Sin Cliente'
            equipo = r.name
            nick = r.nick if r.nick else 'NA'

            acumulador += '<br/><b>Plataforma:</b> ' + platform
            acumulador += '<br/><b>Cliente:</b> ' + client
            acumulador += '<br/><b>Equipo:</b> ' + equipo
            acumulador += '<br/><b>Nick:</b> ' + nick
            acumulador += '<br/><b>Línea:</b> ' + chip

            notify_gps_list += '<br/>' + client + ' || ' + equipo + ' || ' + nick + ' || ' + platform

            # Comprobando funciones adicionales
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
            # Ejecutamos la Baja del Equipo
            r.write({
                'fuel': False,
                'scanner': False,
                'temperature': False,
                'logistic': False,
                'status': "hibernate",
            })

            r.message_post(body=body)

            # revisamos el tema de las suscripciones:
            default = dict(None or {})
            new_subscription = self.env['sale.subscription']
            #template_id = self.env['sale.subscription.template'].search([], limit=1).id
            template_id = suscription_hibernate_template_id
            pricelist_id = self.env['product.pricelist'].search([
                ('currency_id', '=', self.env.user.company_id.currency_id.id)], limit=1).id
            subscription_draft_stage = self.sudo().env.ref(
                'sale_subscription.sale_subscription_stage_draft').ensure_one()

            if not template_id:
                self.message_post(body="<b style='color:red'>AVISO</b>"
                                        "<br>No se pudo crear la subscripción de Hibernación automáticamente en el equipo."
                                        "<br>Deberá crearla manualmente."
                                        "<br>Es probable que ninguna plantilla de subscripción esta activa.")
            else:
                n = new_subscription.create({
                    'name': 'New Subscription',
                    'code': 'Hibernación ' + r.name,
                    'stage_id': subscription_draft_stage.id,
                    'template_id': template_id,
                    'pricelist_id': pricelist_id,
                    'partner_id': r.client_id.id,
                    'gpsdevice_id': r.id,
                })
                skip_subscription_ids.append(n.id)

        self.devices_list = notify_gps_list

        # Alterando las suscripciones encontradas
        suscriptions = self.env['sale.subscription'].search([
            ['gpsdevice_id', 'in', active_records.ids],
            ['id', 'not in', skip_subscription_ids],
        ])

        for s in suscriptions:
            s.message_post(body="El equipo se ha procesado como Hibernado en el sistema.")

        suscriptions.write({'stage_id': suscription_hibernate_stage_id })

        channel_msn = '<br/>Los equipos mencionados a continuación se procesaron para ser hibernados por motivo de:<br/>'
        channel_msn += self.comment + '<br/> soliciato por: ' + self.requeste_by + '<br/>'
        channel_msn += self.devices_list

        poster_bajas = self.sudo().env['mail.channel'].search([('id', '=', channel_id)])
        poster_bajas.message_post(body=channel_msn, subtype='mail.mt_comment', partner_ids=[(4, self.env.uid)])

        return {}
