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
            ('replacement', _('Reemplazo de equipo por garantía')),
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
        domain="[('status', 'in', ['installed', 'demo', 'comodato', 'borrowed']),('platform', '!=', 'Drop')]"
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
            self.execute_drop()
        # Hibernation
        if self.operation_mode == 'hibernation':
            #self.test_create_subscription_from_nowhere()
            self.execute_hibernation()
        # Substitution
        if self.operation_mode == 'substitution':
            self.execute_substitution()
        # Replacement
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
        channel_id = Config.get_param('lgps.device_wizard.drop_default_channel')

        # Log to Channel
        self.log_to_channel(channel_id, channel_msn)
        #_logger.warning('active_recordst: %s', active_records)
        #_logger.warning('active_records: %s', active_records[0])
        #Create Object Log
        self.create_device_log(active_records[0])
        return {}

    def execute_hibernation(self):
        # Check Rules
        self._check_mandatory_fields(['comment', 'requested_by'])

        # LGPS Global Configuration
        LgpsConfig = self.sudo().env['ir.config_parameter']

        subscription_hibernate_stage_id = LgpsConfig.get_param(
            'lgps.device_wizard.hibernate_default_subscription_stage')
        _logger.warning('subscription_hibernate_stage_id: %s', subscription_hibernate_stage_id)
        if not subscription_hibernate_stage_id:
            raise UserError(_(
                'There is not configuration for default channel.\n Configure this in order to send the notification.'))

        subscription_hibernate_template_id = LgpsConfig.get_param(
            'lgps.device_wizard.hibernate_default_subscription_template')
        _logger.warning('subscription_hibernate_template_id: %s', subscription_hibernate_template_id)
        if not subscription_hibernate_template_id:
            raise UserError(_(
                'There is not configuration for default channel.\n Configure this in order to send the notification.'))

        channel_id = LgpsConfig.get_param('lgps.hibernate_device_wizard.default_channel')
        _logger.warning('channel_id: %s', channel_id)
        if not channel_id:
            raise UserError(_(
                'There is not configuration for default channel.\n Configure this in order to send the notification.'))

        hibernate_product_id = LgpsConfig.get_param('lgps.device_wizard.hibernate_default_service')
        _logger.warning('hibernate_product_id: %s', hibernate_product_id)
        if not hibernate_product_id:
            raise UserError(_(
                'There is not configuration for default service.'
                '\n Configure this in order to create subscription successfully.'))
        else:
            product = self.sudo().env['product.product'].search([('id', '=', hibernate_product_id)], limit=1)

        hibernation_commercial_id = LgpsConfig.get_param('lgps.device_wizard.hibernate_commercial_default')
        _logger.warning('hibernation_commercial_id: %s', hibernation_commercial_id)
        if not hibernation_commercial_id:
            raise UserError(_(
                'There is not configuration for default commercial team.'
                '\n Configure this in order to create subscription successfully.'))

        hibernate_user_id = LgpsConfig.get_param('lgps.device_wizard.hibernate_user_default')
        _logger.warning('hibernate_user_id: %s', hibernate_user_id)
        if not hibernate_user_id:
            raise UserError(_(
                'There is not configuration for default user as responsable.'
                '\n Configure this in order to create subscription successfully.'))

        hibernate_price_list_id = LgpsConfig.get_param('lgps.device_wizard.hibernate_default_price_list_id')
        _logger.warning('hibernate_price_list_id: %s', hibernate_price_list_id)
        if not hibernate_price_list_id:
            raise UserError(_(
                'There is not configuration for default price list.'
                '\n Configure this in order to create subscription successfully.'))


        # Obtenemos los Ids seleccionados
        active_model = self._context.get('active_model')
        active_records = self.env[active_model].browse(self._context.get('active_ids'))
        # Subscriptions Config vars

        # Buffer Vars
        notify_gps_list = ""
        skip_subscription_ids = []

        # Procesamos los quipos seleccionados:
        for r in active_records:
            body = "[Proceso de Hibernación]<br/><br/>" + self.comment \
                   + '<br/><b>Solicitado por</b>: ' \
                   + self.requested_by + '<br/>'
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
                'tracking': True,
                'status': "hibernate",
            })

            r.message_post(body=body)

            # Cerramos las suscripciones que tenga el equipo abiertas
            subscription_to_close = r.suscription_id
            if subscription_to_close:
                self._close_subscriptions(subscription_to_close, body)

            # revisamos el tema de las suscripciones:
            default = dict(None or {})
            new_subscription = self.env['sale.subscription']
            #template_id = self.env['sale.subscription.template'].search([], limit=1).id
            template_id = subscription_hibernate_template_id
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
                    'stage_id': subscription_hibernate_stage_id,
                    'template_id': template_id,
                    'pricelist_id': pricelist_id,
                    'partner_id': r.client_id.id,
                    'gpsdevice_id': r.id,
                    'user_id': hibernate_user_id,
                    'team_id': hibernation_commercial_id,
                    'recurring_invoice_line_ids': [(0, _,  {
                        'product_id': product.id,
                        'quantity': 1,
                        'uom_id': product.uom_id.id,
                        'price_unit': self.get_price_from_pricelist(hibernate_price_list_id, product),
                        'name': product.display_name,
                        'discount': 0,
                    })]
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

        suscriptions.write({'stage_id': subscription_hibernate_stage_id })

        channel_msn = '<br/>Los equipos mencionados a continuación se procesaron para ser hibernados por motivo de:<br/>'
        channel_msn += self.comment + '<br/> soliciato por: ' + self.requested_by + '<br/>'
        channel_msn += self.devices_list

        # Send Message
        self.log_to_channel(channel_id, channel_msn)

        self.create_device_log(active_records[0])
        return {}

    def execute_substitution(self):
        lgps_config = self.sudo().env['ir.config_parameter']
        channel_id = lgps_config.get_param('lgps.device_wizard.substitution_default_channel')
        if not channel_id:
            raise UserError(_(
                'There is not configuration for default channel.\n Configure this in order to send the notification.'))

        # Check mandatory fields
        self._check_mandatory_fields(['comment', 'related_odt'])

        # Obtenemos los Ids seleccionados
        active_model = self._context.get('active_model')
        active_records = self.env[active_model].browse(self._context.get('active_ids'))
        subscription_close_stage = self.sudo().env.ref('sale_subscription.sale_subscription_stage_closed')
        subscription_in_progress_stage = self.sudo().env.ref('sale_subscription.sale_subscription_stage_in_progress')

        # Messages to Log on Models
        repair_internal_notes = 'El equipo SUSTITUIDO se sustituyó con el equipo: EQUIPO con la ODT: RELATED_ODT'
        operation_log_comment = 'El equipo <strong>SUSTITUIDO</strong> se retira mientras que esta en revisión con ODT <strong>RMA_ODT</strong>. Se instala el equipo: <strong>EQUIPO</strong> en su lugar con la ODT <strong>RELATED_ODT</strong>. <br/>Se entrega equipo a Soporte para revisión.'
        operation_log_comment_device = 'Se coloca como sustituto al equipo <strong>EQUIPO</strong>  mientras está en revisión con la ODT <strong>RMA_ODT</strong><br/><br/>Comentario: '+self.comment

        for device in active_records:
            if not device.warranty_start_date:
                raise UserError(_('The device does not have Warranty Start Date. Complete this first in order to process the Substitution Operation.'))

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
               'quotation_notes': repair_internal_notes,
               'installer_id': self.related_odt.installer_id.id,
               'assistant_a_id': self.related_odt.assistant_a_id.id,
               'assistant_b_id': self.related_odt.assistant_b_id.id
            })
            # Comments to log on the operation log comment
            repair_internal_notes = repair_internal_notes.replace("RMA_ODT", nodt.name)
            operation_log_comment = operation_log_comment.replace("RMA_ODT", nodt.name)
            operation_log_comment = operation_log_comment.replace("SUSTITUIDO", device.name)
            operation_log_comment = operation_log_comment.replace('EQUIPO', self.destination_gpsdevice_ids.name)
            operation_log_comment = operation_log_comment.replace('RELATED_ODT', self.related_odt.name)

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
                        s.message_post(body='Se cierra suscripción por motivo de: <br/><br/>' + operation_log_comment)
                        _logger.warning('Subscription Recurring invoice line ids: %s', s.recurring_invoice_line_ids)

                        subscription_copy = self.copy_subscription(s, {
                            'name': 'Sustitución ' + self.destination_gpsdevice_ids.name,
                            'code': 'Sustitución ' + self.destination_gpsdevice_ids.name,
                            'stage_id': subscription_in_progress_stage.id,
                            'gpsdevice_id': self.destination_gpsdevice_ids.id,
                        })

                        _logger.warning('subscription_copy: %s', subscription_copy)
                        s.write({'stage_id': subscription_close_stage.id})
                    else:
                        operation_log_comment_device += '<p style="color:red">El equipo sustituido ' + device.name + ' no tenía Suscripción en Progreso.</p>'
            else:
                operation_log_comment_device += '<p style="color:red">El equipo sustituido ' + device.name + ' no tenía Suscripción en Progreso.</p>'

            # Estatus del Equipo como desinstalado
            device.write({'status': "uninstalled"})
            device.message_post(body=operation_log_comment)

            operation_log_comment_device = operation_log_comment_device.replace('EQUIPO', device.name)
            operation_log_comment_device = operation_log_comment_device.replace('RMA_ODT', nodt.name)
            self.destination_gpsdevice_ids.write({'status': "borrowed"})
            self.destination_gpsdevice_ids.message_post(body=operation_log_comment_device)
            self.create_device_log(device)
            self.log_to_channel(channel_id, operation_log_comment)

        return {}

    def execute_replacement(self):
        lgps_config = self.sudo().env['ir.config_parameter']
        channel_id = lgps_config.get_param('lgps.device_wizard.replacement_default_channel')
        if not channel_id:
            raise UserError(_(
                'There is not configuration for default channel.\n Configure this in order to send the notification.'))
        self._check_mandatory_fields(['comment', 'related_odt'])

        # Obtenemos los Ids seleccionados
        active_model = self._context.get('active_model')
        active_records = self.env[active_model].browse(self._context.get('active_ids'))
        subscription_close_stage = self.sudo().env.ref('sale_subscription.sale_subscription_stage_closed')
        subscription_in_progress_stage = self.sudo().env.ref('sale_subscription.sale_subscription_stage_in_progress')

        repair_internal_notes = 'El equipo REEMPLAZADO se reemplazó con el equipo: EQUIPO con la ODT: RELATED_ODT'
        operation_log_comment = 'El equipo <strong>REEMPLAZADO</strong> se reemplaza con el equipo <strong>EQUIPO</strong> con número de ODT <strong>RELATED_ODT</strong>. <br/>El equipo pasa a propiedad de la empresa.<br/>Se entrega equipo a Soporte para revisión.<br/><br/>Comentario: '+self.comment
        operation_log_comment_device = 'Se coloca equipo como reemplazo para el equipo <strong>EQUIPO</strong>  con la ODT <strong>RELATED_ODT</strong><br/><br/>Comentario: '+self.comment

        for device in active_records:
            if not device.warranty_start_date:
                raise UserError(_('The device does not have Warranty Start Date. Complete this first in order to process the Replacement Operation.'))

            # Preparando Datos para la suscripcion
            product_id = device.product_id
            serialnumber_id = device.serialnumber_id
            client_id = self.env.user.company_id
            device_id = device.id

            repair_internal_notes = repair_internal_notes.replace("REEMPLAZADO", device.name)
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
               'quotation_notes': repair_internal_notes,
               'installer_id': self.related_odt.installer_id.id,
               'assistant_a_id': self.related_odt.assistant_a_id.id,
               'assistant_b_id': self.related_odt.assistant_b_id.id
            }
            nodt = self.create_odt(dictionary)

            # Cerramos las Suscripciones del equipo que sustituye
            subscription_to_close = self.destination_gpsdevice_ids.suscription_id
            if subscription_to_close:
                self._close_subscriptions(subscription_to_close, repair_internal_notes)

            operation_log_comment = operation_log_comment.replace("REEMPLAZADO", device.name)
            operation_log_comment = operation_log_comment.replace('EQUIPO', self.destination_gpsdevice_ids.name)
            operation_log_comment = operation_log_comment.replace('RELATED_ODT', self.related_odt.name)

            # Check subscriptions
            if device.suscription_id:
                # Recorremos las suscripciones asociadas al equipos GPS.
                for s in device.suscription_id:
                    # Si alguna subscripción esta en progreso vamos a copiarla:
                    if s.stage_id.id == subscription_in_progress_stage.id:
                        s.message_post(body='Se cierra suscripción por motivo de: <br/><br/>' + operation_log_comment)
                        _logger.warning('Subscription Recurring invoice line ids: %s', s.recurring_invoice_line_ids)

                        subscription_copy = self.copy_subscription(s, {
                            'name': 'Sustitución ' + self.destination_gpsdevice_ids.name,
                            'code': 'Sustitución ' + self.destination_gpsdevice_ids.name,
                            'stage_id': subscription_in_progress_stage.id,
                            'gpsdevice_id': self.destination_gpsdevice_ids.id,
                        })

                        _logger.warning('subscription_copy: %s', subscription_copy)
                        s.write({'stage_id': subscription_close_stage.id})
                    else:
                        operation_log_comment_device += '<p style="color:red">El equipo reemplazado ' + device.name + ' no tenía Suscripción en Progreso.</p>'
            else:
                operation_log_comment_device += '<p style="color:red">El equipo reemplazado ' + device.name + ' no tenía Suscripción en Progreso.</p>'

            operation_log_comment_device = operation_log_comment_device.replace('EQUIPO', device.name)
            operation_log_comment_device = operation_log_comment_device.replace('RELATED_ODT', self.related_odt.name)
            operation_log_comment_device += '<br/>Fecha de garantía de <strong>' \
                                            + self.destination_gpsdevice_ids.warranty_start_date.strftime('%Y-%m-%d') \
                                            + '</strong> a <strong>' + device.warranty_start_date.strftime('%Y-%m-%d') + '</strong>'

            # Estatus del Equipo como desinstalado
            device.write({'status': "uninstalled", "client_id": self.env.user.company_id.id})
            device.message_post(body=operation_log_comment)
            self.create_device_log(device)
            self.log_to_channel(channel_id, operation_log_comment)

            self.destination_gpsdevice_ids.write({'warranty_start_date': device.warranty_start_date})
            self.destination_gpsdevice_ids.message_post(body=operation_log_comment_device)

        return {}

    def get_price_from_pricelist(self, price_list, product):

        pricelist = self.sudo().env['product.pricelist'].search([('id', '=', price_list)], limit=1)
        price = pricelist.get_product_price(product, 1, False)
        if price:
            return price
        else:
            return product.lst_price

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

    def _get_error_message_for_field(self, field=''):
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
                subscription.message_post(body='Se cierra suscripción por motivo de: <br>' + comment)
        return True

    def create_device_log(self, device):
        log_object = self.env['lgps.device_history']

        dictionary = {
            'name': device.name + ' - ' + self.operation_mode,
            'product_id': device.product_id.id,
            'serialnumber_id': device.serialnumber_id.id,
            'client_id': device.client_id.id,
            'gpsdevice_ids': device.id,
            'destination_gpsdevice_ids': self.destination_gpsdevice_ids.id,
            'product_id': device.product_id.id,
            'operation_mode': self.operation_mode,
            'related_odt': self.related_odt.id,
            'requested_by': self.requested_by,
            'comment': self.comment
        }
        device_log = log_object.create(dictionary)
        return device_log

    def log_to_channel(self, channel_id, channel_msn):

        if not channel_id:
           raise UserError(_('There is not configuration for default channel.\n Configure this in order to send the notification.'))
        else:
            channel_notifier = self.sudo().env['mail.channel'].search([('id', '=', channel_id)])
            channel_notifier.message_post(body=channel_msn, subtype='mail.mt_comment', partner_ids=[(4, self.env.uid)])

        return {}
