# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from odoo.exceptions import UserError
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

        # Obtenemos los Ids seleccionados
        active_model = self._context.get('active_model')
        active_records = self.env[active_model].browse(self._context.get('active_ids'))
        # Buffer Vars
        notify_gps_list = ""
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
            r.message_post(body=body)

            # revisamos el tema de las suscripciones:
            if r.suscription_id:

                ReccurringInvoiveLine = self.env['sale.subscription.line']

                #ReccurringInvoiveLine.create({
                #                    'product_id': r.suscription_id.recurring_invoice_line_ids.product_id and r.suscription_id.recurring_invoice_line_ids.product_id.id or False,
                #                    'quantity': r.suscription_id.recurring_invoice_line_ids.quantity,
                #                    'uom_id': r.suscription_id.recurring_invoice_line_ids.uom_id.id,
                #                    'price_unit': r.suscription_id.recurring_invoice_line_ids.price_unit,
                #                    'name': r.suscription_id.recurring_invoice_line_ids.name,
                    #'discount': r.suscription_id.recurring_invoice_line_ids.discount,
                    #'account_id': r.suscription_id.recurring_invoice_line_ids.account_id.id,
                    #'invoice_line_tax_ids': [(6, 0, r.suscription_id.recurring_invoice_line_ids.invoice_line_tax_ids.ids)]
                #})

                default = dict(None or {})
                subscription_draft_stage = self.sudo().env.ref('sale_subscription.sale_subscription_stage_draft').ensure_one()
                _logger.warning('subscription_draft_stage [%s]', subscription_draft_stage.id)

                default['name'] = 'Hibernado ' + r.suscription_id.display_name
                default['stage_id'] = subscription_draft_stage.id
                default['code']
                #default['company_id']
                #default['currency_id']
                #default['gpsdevice_id']
                #default['partner_id']
                #default['pricelist_id']
                #default['pricelist_id']

                #default['recurring_invoice_line_ids'] = [(6, 0, ReccurringInvoiveLine.id)]
                #r.suscription_id.recurring_invoice_line_ids

                suscription_copy = r.suscription_id.copy(default)
                _logger.warning('Display Name [%s]', suscription_copy.display_name)
                _logger.warning('stage_id [%s]', subscription_draft_stage.id)


        # Ejecutamos la Baja en el sistema
        active_records.write({
            'fuel': False,
            'scanner': False,
            'temperature': False,
            'logistic': False,
            'status': "hibernate",
        })

        self.devices_list = notify_gps_list

        # Alterando las suscripciones
        suscription_close_stage = self.sudo().env.ref('sale_subscription.sale_subscription_stage_closed')
        suscriptions = self.env['sale.subscription'].search([['gpsdevice_id', 'in', active_records.ids]])
        for s in suscriptions:
            s.message_post(body="El equipo se ha dado de procesado como Hibernado en el sistema.")
        suscriptions.write({'stage_id': suscription_close_stage.id})

        channel_msn = '<br/>Los equipos mencionados a continuación se procesaron para ser hibernados por motivo de:<br/>'
        channel_msn += self.comment + '<br/> soliciato por: ' + self.requeste_by + '<br/>'
        channel_msn += self.devices_list

        Config = self.env['ir.config_parameter']
        channel_id = Config.get_param('lgps.hibernate_device_wizard.default_channel')
        if not channel_id:
           raise UserError(_('There is not configuration for default channel.\n Configure this in order to send the notification.'))
        else:
            poster_bajas = self.sudo().env['mail.channel'].search([('id', '=', channel_id)])
            poster_bajas.message_post(body=channel_msn, subtype='mail.mt_comment', partner_ids=[(4, self.env.uid)])

        return {}
