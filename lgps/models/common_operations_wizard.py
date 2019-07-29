# -*- coding: utf-8 -*-
from datetime import timedelta
from odoo import api, models, fields, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class CommonOperationsToDevicesWizard(models.TransientModel):
    _name = "lgps.common_operations_device_wizard"
    _description = "Common Operations To Devices Wizard"

    def _default_gpsdevices(self):
        return self.env['lgps.gpsdevice'].browse(self._context.get('active_ids'))

    operation_mode = fields.Selection(
        [
            ('drop', _('Baja de Equipos')),
            ('hibernation', _('Hibernación de Equipos')),
            ('replacement', _('Reemplazo de Equipo')),
            ('substitution', _('Sustitución de equipo por revisión')),
        ],
        default='drop'
    )

    gpsdevice_ids = fields.Many2many(
        comodel_name='lgps.gpsdevice',
        string="Gps Device",
        required=True,
        default=_default_gpsdevices,
    )

    destination_gpsdevice_ids = fields.Many2one(
        comodel_name='lgps.gpsdevice',
        string="Substitute equipment",
        domain="[('status', 'in', ['installed', 'demo', 'comodato']),('platform', '!=', 'Drop')]"
    )

    related_odt = fields.Many2one(
        comodel_name='repair.order',
        string=_("Work order related"),
    )

    requested_by = fields.Char(
        string=_("Requested by"),
    )

    comment = fields.Text(
        string=_("Operation Reason"),
        required=True,
    )

    devices_list = fields.Text(
        string=_("Devices List")
    )

    cellchips_list = fields.Text(
        string=_("Cellchips List")
    )


    @api.multi
    def execute_operation(self):
        if len(self._context.get('active_ids')) < 1:
            raise UserError(_('Select at least one record.'))

        # Determinamos el tipo de Operació a Realizar
        if self.operation_mode == 'drop':
            #self.execute_drop()
            self.testing_suscription()
        # Hibernation
        if self.operation_mode == 'hibernation':
            self.execute_hibernation()

        if self.operation_mode == 'substitution':
            self.execute_substitution()

        if self.operation_mode == 'replacement':
            self.execute_replacement()

        return {}

    def execute_drop(self):
        # Obtenemos los Ids seleccionados
        active_model = self._context.get('active_model')
        active_records = self.env[active_model].browse(self._context.get('active_ids'))

        # Buffer Vars
        cellchips_ids = []
        notify_cellchisp_list = ""
        notify_gps_list = ""
        requested_by = self.requested_by

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

    def execute_hibernation(self):
        if len(self._context.get('active_ids')) < 1:
            raise UserError(_('Select at least one record.'))
        if not self.comment:
            raise UserError(_('You forgot to comment the reason for this process to run.'))
        if not self.requested_by:
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
            body = "[Proceso de Hibernación]<br/><br/>" + self.comment + '<br/><b>Solicitado por</b>: ' + self.requested_by + '<br/>'
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
        channel_msn += self.comment + '<br/> soliciato por: ' + self.requested_by + '<br/>'
        channel_msn += self.devices_list

        poster_bajas = self.sudo().env['mail.channel'].search([('id', '=', channel_id)])
        poster_bajas.message_post(body=channel_msn, subtype='mail.mt_comment', partner_ids=[(4, self.env.uid)])

        return {}

    def execute_substitution(self):
        # Check mandatory fields
        self._check_mandatory_fields(['comment', 'related_odt'])

        # LGPS Global Configuration
        LgpsConfig = self.sudo().env['ir.config_parameter']
        equipo_en_susticion = self.destination_gpsdevice_ids.name

        # Obtenemos los Ids seleccionados
        active_model = self._context.get('active_model')
        active_records = self.env[active_model].browse(self._context.get('active_ids'))
        subscription_close_stage = self.sudo().env.ref('sale_subscription.sale_subscription_stage_closed')
        subscription_in_progress_stage = self.sudo().env.ref('sale_subscription.sale_subscription_stage_in_progress')

        # Messages to Log on Models
        repair_internal_notes = 'El equipo SUSTITUIDO se sustituyó con el equipo: EQUIPO con la ODT: RELATED_ODT'
        operation_log_comment = 'Se realiza sustitución con el equipo: <strong>EQUIPO</strong>, mientras que este está en revisión con ODT <strong>RELATED_ODT</strong>. <br/>Se entrega equipo a Soporte para revisión.'
        operation_log_comment_device = 'Se coloca como sustituto al equipo <strong>EQUIPO</strong>  mientras está en revisión con la ODT <strong>RELATED_ODT</strong><br/><br/>Comentario: '+self.comment
        #_logger.warning('self.gpsdevice_ids.name %s', self.gpsdevice_ids.name)
        suscription_copy = None

        # Cerrar suscripión OK
        # Estatus desinstalado OK
        # Comentario OK
        # Generar ODT
        for device in active_records:

            # Preparando Datos para la ODT
            product_id = device.product_id
            serialnumber_id = device.serialnumber_id
            client_id = device.client_id
            device_id = device.id

            repair_internal_notes = repair_internal_notes.replace("SUSTITUIDO", device.name)
            repair_internal_notes = repair_internal_notes.replace("EQUIPO", self.destination_gpsdevice_ids.name)
            repair_internal_notes = repair_internal_notes.replace("RELATED_ODT", self.related_odt.name)

            odt_name = self.env['ir.sequence'].sudo().next_by_code('repair.order')
            odt_name = odt_name.replace('ODT', 'RMA')

            odt_object = self.env['repair.order']
            nodt = self.create_odt({
               'name': odt_name,
               'product_id': product_id.id,
               'product_qty': 1,
               'lot_id': serialnumber_id.id,
               'partner_id': client_id.id,
               'gpsdevice_id': device_id,
               'invoice_method': "after_repair",
               'product_uom': product_id.uom_id.id,
               'location_id': odt_object._default_stock_location(),
               'pricelist_id': self.env['product.pricelist'].search([], limit=1).id,
               'internal_notes': repair_internal_notes,
            })
            # Comments to log on the operation log comment
            operation_log_comment = operation_log_comment.replace('EQUIPO', self.destination_gpsdevice_ids.name)
            operation_log_comment = operation_log_comment.replace('RELATED_ODT', nodt.name)

            # Cerramos las Suscripciones del equipo que sustituye
            subscription_to_close = self.destination_gpsdevice_ids.suscription_id
            if subscription_to_close:
                self._close_subscriptions(subscription_to_close, repair_internal_notes)

            # Check subscriptions
            if device.suscription_id:
                # Recorremos las suscripciones asociadas al equipos GPS.
                for s in device.suscription_id:
                    # Si alguna subscripción esta en progreso vamos a copiarla:
                    if s.stage_id.id == subscription_in_progress_stage.id:
                        s.message_post(body=operation_log_comment)
                        _logger.warning('Subscription Recurring invoice line ids: %s', s.recurring_invoice_line_ids)

                        subscription_copy = self.copy_subscription(s, {
                            'name': 'Sustitución ' + self.destination_gpsdevice_ids.name,
                            'stage_id': subscription_in_progress_stage.id,
                            'gpsdevice_id': self.destination_gpsdevice_ids.id,
                        })

                        _logger.warning('subscription_copy: %s', subscription_copy)
                        s.write({'stage_id': subscription_close_stage.id})
                    else:
                        operation_log_comment_device += '<p style="color:red">El equipo sustituido ' + device.name + ' no tenía Suscripción en Progreso.</p>'


            # Estatus del Equipo como desinstalado
            device.write({'status': "uninstalled"})
            device.message_post(body=operation_log_comment)

            #_logger.error('Suscription: %s', device.suscription_id)
            operation_log_comment_device = operation_log_comment_device.replace('EQUIPO', device.name)
            operation_log_comment_device = operation_log_comment_device.replace('RELATED_ODT', nodt.name)
            self.destination_gpsdevice_ids.write({'status': "borrowed"})
            self.destination_gpsdevice_ids.message_post(body=operation_log_comment_device)

        return {}

    def execute_replacement(self):

        self._check_mandatory_fields(['comment', 'related_odt'])
        # LGPS Global Configuration
        LgpsConfig = self.sudo().env['ir.config_parameter']
        equipo_en_susticion = self.destination_gpsdevice_ids.name

        # Obtenemos los Ids seleccionados
        active_model = self._context.get('active_model')
        active_records = self.env[active_model].browse(self._context.get('active_ids'))
        suscription_close_stage = self.sudo().env.ref('sale_subscription.sale_subscription_stage_closed')
        suscription_in_progress_stage = self.sudo().env.ref('sale_subscription.sale_subscription_stage_in_progress')
        #_logger.error('Suscription Closed Stage: %s', suscription_close_stage)

        repair_internal_notes = 'Se reemplaza equipo por EQUIPO con la ODT: RELATED_ODT'
        operation_log_comment = 'Se reemplaza con el equipo <strong>EQUIPO</strong> con número de ODT <strong>RELATED_ODT</strong>. <br/>El equipo pasa a propiedad de la empresa.<br/>Se entrega equipo a Soporte para revisión.<br/><br/>Comentario: '+self.comment
        operation_log_comment_device = 'Se coloca equipo como reemplazo por el equipo <strong>EQUIPO</strong>  con la ODT <strong>RELATED_ODT</strong><br/><br/>Comentario: '+self.comment
        operation_log_comment_subscriptions = 'Se cierra por que el equipo fué reemplazado con el equipo <strong>EQUIPO</strong>  con la ODT <strong>RELATED_ODT</strong><br/><br/>'
        #_logger.warning('self.gpsdevice_ids.name %s', self.gpsdevice_ids.name)
        suscription_copy = None

        # Cerrar suscripión OK
        # Estatus desinstalado OK
        # Comentario OK
        # Generar ODT
        for device in active_records:
            if not device.warranty_start_date:
                raise UserError(_('The device does not have Warranty Start Date. Complete this first in order to process the Replacement Operation.'))

            # Preparando Datos para la suscripcion
            product_id = device.product_id
            serialnumber_id = device.serialnumber_id
            client_id = self.env.user.company_id
            device_id = device.id

            repair_internal_notes = repair_internal_notes.replace("EQUIPO", self.destination_gpsdevice_ids.name)
            repair_internal_notes = repair_internal_notes.replace("RELATED_ODT", self.related_odt.name)

            odt_name = self.env['ir.sequence'].sudo().next_by_code('repair.order')
            odt_name = odt_name.replace('ODT', 'RMA')

            odt_object = self.env['repair.order']
            dictionary = {
               'name': odt_name,
               'product_id': product_id.id,
               'product_qty': 1,
               'lot_id': serialnumber_id.id,
               'partner_id': client_id.id,
               'gpsdevice_id': device_id,
               'invoice_method': "after_repair",
               'product_uom': product_id.uom_id.id,
               'location_id': odt_object._default_stock_location(),
               'pricelist_id': self.env['product.pricelist'].search([], limit=1).id,
               'internal_notes': repair_internal_notes,
            }
            nodt = self.create_odt(dictionary)


            if device.suscription_id:
                if device.suscription_id.stage_id == suscription_in_progress_stage.id:
                    device.suscription_id.message_post(body=operation_log_comment)
                    suscription_copy = device.suscription_id.copy(default={
                        'name': 'Sustitución ' + self.destination_gpsdevice_ids.name,
                        'stage_id': suscription_in_progress_stage.id,
                        'gpsdevice_id': self.destination_gpsdevice_ids.id
                    })
                    _logger.warning('suscription_copy: %s', suscription_copy)
            else:
                operation_log_comment_device += '<p style="color:red">El equipo reemplazado no tenía Suscripción en progreso.</p>'

            device.suscription_id.write({'stage_id': suscription_close_stage.id})

            operation_log_comment = operation_log_comment.replace('EQUIPO', self.destination_gpsdevice_ids.name)
            operation_log_comment = operation_log_comment.replace('RELATED_ODT', self.related_odt.name)

            operation_log_comment_device = operation_log_comment_device.replace('EQUIPO', device.name)
            operation_log_comment_device = operation_log_comment_device.replace('RELATED_ODT', self.related_odt.name)
            _logger.warning('self.destination_gpsdevice_ids.warranty_start_date: %s', self.destination_gpsdevice_ids.warranty_start_date)
            _logger.warning('device.warranty_start_date: %s', device.warranty_start_date)
            operation_log_comment_device += '<br/>Fecha de garantía de <strong>' \
                                            + self.destination_gpsdevice_ids.warranty_start_date.strftime('%Y-%m-%d') \
                                            + '</strong> a <strong>' + device.warranty_start_date.strftime('%Y-%m-%d') + '</strong>'

            # Estatus del Equipo como desinstalado
            device.write({'status': "uninstalled", "client_id": self.env.user.company_id.id})
            device.message_post(body=operation_log_comment)

            #_logger.error('Suscription: %s', device.suscription_id)
            self.destination_gpsdevice_ids.write({'warranty_start_date': device.warranty_start_date})
            self.destination_gpsdevice_ids.message_post(body=operation_log_comment_device)

        return {}

    def testing_suscription(self):
        """
        InvLine = self.env['sale.subscription.line']
        active_model = self._context.get('active_model')
        active_records = self.env[active_model].browse(self._context.get('active_ids'))
        for device in active_records:
            if device.suscription_id:
                for suscription in device.suscription_id:
                    suscription_copy = suscription.copy(default={
                        'name': 'Sustitución' + device.name,
                        #'stage_id': device.suscription_id.recurring_invoice_line_ids.id,
                        'gpsdevice_id': device.id
                    })

                    _logger.warning('SUSCRIPTION Recurring invoice line ids: %s', suscription)
                    invoice_lines = suscription.recurring_invoice_line_ids
                    _logger.warning('invoice_lines: %s', invoice_lines)
                    for line in invoice_lines:
                        #line_copy = line.copy(default={})
                        #_logger.warning('Line: %s', line)
                        #_logger.warning('line_copy: %s', line_copy)
                        _logger.warning('Line: %s', line)
                        _logger.warning('Line ​display_name: %s', line.display_name)
                        _logger.warning('Line id: %s', line.id)
                        _logger.warning('Line product_id: %s', line.product_id)
                        _logger.warning('Line quantity: %s', line.quantity)
                        _logger.warning('Line uom_id: %s', line.uom_id)
                        _logger.warning('Line price_unit: %s', line.price_unit)
                        _logger.warning('Line name: %s', line.name)
                        _logger.warning('Line discount: %s', line.discount)
                        _logger.warning('Line ​price_subtotal: %s', line.price_subtotal)
                        _logger.warning('Line ​price_unit: %s', line.price_unit)
                        #InvLine.create({
                        #   'product_id': line.product_id and line.product_id.id or False,
                        #   'quantity': line.quantity,
                        #   'uom_id': line.uom_id.id,
                        #   'price_unit': line.price_unit,
                        #   'name': line.name,
                        #   'display_name': line.name,
                        #   'discount': line.discount,
                        #   'price_subtotal': line.price_subtotal,
                        #})
                        #suscription_copy.recurring_invoice_line_ids = [(0, 0, {
                        #    'product_id': line.product_id and line.product_id.id or False,
                        #  'quantity': line.quantity,
                        #  'uom_id': line.uom_id.id,
                        #  'price_unit': line.price_unit,
                        #  'name': line.name,
                        #  'display_name': line.name,
                        #  'discount': line.discount,
                        #  'price_subtotal': line.price_subtotal,
                        #})]
                        #_logger.warning('line_copy: %s', InvLine)
        """
        return {}

    def create_odt(self, dictionary):
        odt_object = self.env['repair.order']
        odt = odt_object.create(dictionary)
        return odt

    def copy_subscription(self, original, default_values):
        subscription_copy = original.copy(default=default_values)
        _logger.warning('subscription_copy: %s', subscription_copy)
        return subscription_copy

    def _check_mandatory_fields(self, rules):
        for rule in rules:

            if not getattr(self, rule):
                raise UserError(self._get_error_message_for_field(rule))

    def _get_error_message_for_field(self, field):
        if field == 'comment':
            return _('You forgot to comment the reason for this process to run.')
        if field == 'requested_by':
            return _('Who authorizes this request?')
        if field == 'related_odt':
            return _('You forgot to select the Related ODT')

    def _close_subscriptions(self, subscriptions, comment=''):
        subscription_close_stage = self.sudo().env.ref('sale_subscription.sale_subscription_stage_closed')
        for subscription in subscriptions:
            subscription.write({'stage_id': subscription_close_stage.id})
            if comment != '':
                subscription.message_post(body='Se cierra suscripcion por motivo de: <br>' + comment)
        return True
