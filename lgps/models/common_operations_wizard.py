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
            ('wakeup', _('Deshibernación de Equipos')),
            ('replacement', _('Reemplazo de equipo por garantía')),
            ('substitution', _('Sustitución de equipo por revisión')),
            ('add_reactivate', _('Alta / Reactivación Equipo')),
            ('loan_substitution', _('Reemplazo de Comodato'))
        ],
        default='drop'
    )

    reason = fields.Selection(
        [
            ('bad_service', _('Mal Servicio')),
            ('vehicle_sold', _('Venta de Unidad')),
            ('wrecked_vehicle', _('Unidad siniestrada')),
            ('client_warehouse', _('Sin uso, en resguardo con el cliente')),
            ('own_warehouse', _('Error administrativo')),
            ('non_repairable', _('Equipo gps no reparable')),
            ('financial_situation', _('Cancelación de cuenta por falta de pago')),
            ('change_of_supplier', _('Cambio de proveedor por precio')),
            ('return_to_stock', _('Regresa a Almacén Respaldo/Provisional/Prestado')),
            ('return_from_loan', _('Regresa a Almacén Estuvo en Comodato')),
            ('on_stock_not_assigned', _('En almacén Intralix sin asignación')),
            ('replacement', _('Por reemplazo de Equipo')),
        ],
    )

    gpsdevice_ids = fields.Many2many(
        comodel_name='lgps.gpsdevice',
        string="Gps Device",
        required=True,
        default=_default_gpsdevices,
    )

    destination_gpsdevice_ids = fields.Many2one(
        comodel_name='lgps.gpsdevice',
        string=_("Substitute equipment"),
        domain="[('status', 'in', ['installed', 'demo', 'comodato', 'borrowed','replacement']),('platform', '!=', 'Drop')]"
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

    # Available services
    tracking = fields.Boolean(default=False, string=_("Tracking"))
    fuel = fields.Boolean(default=False, string=_("Fuel"))
    scanner = fields.Boolean(default=False, string="Scanner")
    temperature = fields.Boolean(default=False, string=_("Temperature"))
    logistic = fields.Boolean(default=False, string=_("Logistic"))
    fleetrun = fields.Boolean(default=False, string=_("Fleetrun"))
    device_status = fields.Selection(
        selection=[
            ("drop", _("Drop")),
            ("comodato", _("Comodato")),
            ("courtesy", _("Courtesy")),
            ("demo", _("Demo")),
            ("uninstalled", _("Uninstalled")),
            ("external", _("External")),
            ("hibernate", _("Hibernate")),
            ("installed", _("Installed")),
            ("inventory", _("Inventory")),
            ("new", _("New")),
            ("for installing", _("For Installing")),
            ("borrowed", _("Borrowed")),
            ("tests", _("Tests")),
            ("replacement", _("Replacement")),
            ("backup", _("Backup")),
            ("rma", _("RMA")),
            ("sold", _("Sold")),
        ],
        default="inventory",
        string=_("Status"),
    )

    platform = fields.Selection(
        selection=[
            ("Ceiba2", "Ceiba2"),
            ("Cybermapa", "Cybermapa"),
            ("Drop", _("Drop")),
            ("Gurtam", "Gurtam"),
            ("Gurtam_Utrax", "Gurtam/Utrax"),
            ("Lkgps", "Lkgps"),
            ("Mapaloc", "Mapaloc"),
            ("Novit", "Novit"),
            ("Position Logic", "Position Logic"),
            ("Sosgps", "Sosgps"),
            ("Utrax", "Utrax"),
        ],
        string=_("Platform"),
    )

    cellchip_id = fields.Many2one(
        comodel_name="lgps.cellchip",
        string=_("Cellchip Number"),
    )

    reactivation_reason = fields.Selection(
        [
            ('op1', _('Alta de equipo para pedido de venta')),
            ('op2', _('Alta de equipo para pruebas')),
            ('op3', _('Equipo como respaldo')),
            ('op4', _('Equipo como préstamo')),
            ('op5', _('Revisión de equipo')),
            ('op6', _('Solicitud de reactivación')),
        ],
        string=_("Motivo del Alta / Reactivación"),
        default="op1"
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
            self.execute_hibernation()
        # Replacement
        if self.operation_mode == 'replacement':
            self.execute_replacement()
        # Substitution
        if self.operation_mode == 'substitution':
            self.execute_substitution()
        # Wakeup
        if self.operation_mode == 'wakeup':
            self.execute_wakeup()
        # Reactivate
        if self.operation_mode == 'add_reactivate':
            self.execute_add_reactivate()
        # Loan Substitution
        if self.operation_mode == 'loan_substitution':
            self.execute_loan_substitution()
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
            additional_functions = False

            platform = r.platform if r.platform else 'Sin Plataforma'
            chip = r.cellchip_id.name if r.cellchip_id else 'Sin chip'
            pchip = r.cellchip_id.provider if r.cellchip_id else 'Sin chip'
            client = r.client_id.name if r.client_id else 'Sin Cliente'
            equipo = r.name
            nick = r.nick if r.nick else 'NA'
            reason = dict(self._fields['reason']._description_selection(self.env)).get(self.reason)

            acumulador += '<br/><b>Motivo:</b> ' + reason
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
                additional_functions = True
                gps_functions_summary += "Rastreo<br/>"
            if r.fuel:
                additional_functions = True
                gps_functions_summary += "Combustible<br/>"
            if r.scanner:
                additional_functions = True
                gps_functions_summary += "Escánner<br/>"
            if r.temperature:
                additional_functions = True
                gps_functions_summary += "Temperatura<br/>"
            if r.logistic:
                additional_functions = True
                gps_functions_summary += "Logística<br/>"
            if r.fleetrun:
                additional_functions = True
                gps_functions_summary += "Mantenimiento de Flotilla<br/>"

            body += '<br/>' + acumulador
            if additional_functions:
                body += gps_functions_summary

            r.message_post(body=body)
            # Create Object Log
            self.create_device_log(r, body)

        # Ejecutamos la Baja en el sistema
        active_records.write({
            'tracking': False,
            'fuel': False,
            'scanner': False,
            'temperature': False,
            'logistic': False,
            'fleetrun': False,
            'platform': "Drop",
            'notify_offline': False,
        })

        self.cellchips_list = notify_cellchisp_list
        self.devices_list = notify_gps_list

        # Alterando las suscripciones
        subscriptions = self.env['sale.subscription'].search([['gpsdevice_id', 'in', active_records.ids]])
        if subscriptions:
            self._change_subscriptions_stage(subscriptions, "El equipo se ha dado de baja en el sistema.")

        # Log para Internos
        channel_msn = '<br/>Los equipos mencionados a continuación se procesaron para dar de baja por motivo de:<br/>'
        channel_msn += self.comment + '<br/>'
        channel_msn += self.devices_list
        channel_msn += '<br/><br/>Se requiere dar de baja la siguientes líneas:<br/>'
        channel_msn += self.cellchips_list

        # Log to Channel
        lgps_config = self.sudo().env['ir.config_parameter']
        channel_id = lgps_config.get_param('lgps.device_wizard.drop_default_channel')
        self.log_to_channel(channel_id, channel_msn)

        return {}

    def execute_hibernation(self):
        # Check Rules
        self._check_mandatory_fields(['comment', 'requested_by'])

        # Obtenemos los Ids seleccionados
        active_model = self._context.get('active_model')
        active_records = self.env[active_model].browse(self._context.get('active_ids'))

        # LGPS Global Configuration
        subscription_close_stage = self.sudo().env.ref('sale_subscription.sale_subscription_stage_closed')

        # LGPS Global Configuration
        lgps_config = self.sudo().env['ir.config_parameter']

        subscription_hibernate_stage_id = lgps_config.get_param(
            'lgps.device_wizard.hibernate_default_subscription_stage')
        #_logger.warning('subscription_hibernate_stage_id: %s', subscription_hibernate_stage_id)
        if not subscription_hibernate_stage_id:
            raise UserError(_(
                'There is not configuration for default stage on new subscription.\nConfigure this in order to send the notification.'))

        subscription_current_hibernate_stage_id = lgps_config.get_param(
            'lgps.device_wizard.hibernate_current_subscription_stage')
        #_logger.warning('subscription_hibernate_stage_id: %s', subscription_hibernate_stage_id)
        if not subscription_current_hibernate_stage_id:
            raise UserError(_(
                'There is not configuration for default current subscriptions stage.\nConfigure this in order to send the notification.'))

        subscription_hibernate_template_id = lgps_config.get_param(
            'lgps.device_wizard.hibernate_default_subscription_template')
        #_logger.warning('subscription_hibernate_template_id: %s', subscription_hibernate_template_id)
        if not subscription_hibernate_template_id:
            raise UserError(_(
                'There is not configuration for default channel.\n Configure this in order to send the notification.'))

        channel_id = lgps_config.get_param('lgps.hibernate_device_wizard.default_channel')
        #_logger.warning('lgps_default_channel_id: %s', lgps_default_channel_id)
        if not channel_id:
            raise UserError(_(
                'There is not configuration for default channel.\n Configure this in order to send the notification.'))

        hibernate_product_id = lgps_config.get_param('lgps.device_wizard.hibernate_default_service')
        #_logger.warning('hibernate_product_id: %s', hibernate_product_id)
        if not hibernate_product_id:
            raise UserError(_(
                'There is not configuration for default service.'
                '\n Configure this in order to create subscription successfully.'))
        else:
            product = self.sudo().env['product.product'].search([('id', '=', hibernate_product_id)], limit=1)

        hibernation_commercial_id = lgps_config.get_param('lgps.device_wizard.hibernate_commercial_default')
        #_logger.warning('hibernation_commercial_id: %s', hibernation_commercial_id)
        if not hibernation_commercial_id:
            raise UserError(_(
                'There is not configuration for default commercial team.'
                '\n Configure this in order to create subscription successfully.'))

        hibernate_user_id = lgps_config.get_param('lgps.device_wizard.hibernate_user_default')
        #_logger.warning('hibernate_user_id: %s', hibernate_user_id)
        if not hibernate_user_id:
            raise UserError(_(
                'There is not configuration for default user as responsable.'
                '\n Configure this in order to create subscription successfully.'))

        hibernate_price_list_id = lgps_config.get_param('lgps.device_wizard.hibernate_default_price_list_id')
        #_logger.warning('hibernate_price_list_id: %s', hibernate_price_list_id)
        if not hibernate_price_list_id:
            raise UserError(_(
                'There is not configuration for default price list.'
                '\n Configure this in order to create subscription successfully.'))

        # Buffer Vars
        notify_gps_list = ""
        skip_subscription_ids = []

        # Procesamos los quipos seleccionados:
        for r in active_records:
            body = "[Proceso de Hibernación]<br/><br/>"
            body += self.comment + '<br/><b>Solicitado por</b>: '
            body += self.requested_by + '<br/>'
            gps_functions_summary = "<hr/>Se desactivaron las funciones de:<br/><br/>"
            acumulador = ""
            additional_functions = False

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
                additional_functions = True
                gps_functions_summary += "Combustible<br/>"
            if r.scanner:
                additional_functions = True
                gps_functions_summary += "Escánner<br/>"
            if r.temperature:
                additional_functions = True
                gps_functions_summary += "Temperatura<br/>"
            if r.logistic:
                additional_functions = True
                gps_functions_summary += "Logística<br/>"
            if r.fleetrun:
                additional_functions = True
                gps_functions_summary += "Mantenimiento de Flotilla<br/>"

            body += '<br/>' + acumulador
            if additional_functions:
                body += gps_functions_summary
            # Desactivamos funciones e hibernamos
            r.write({
                'fuel': False,
                'scanner': False,
                'temperature': False,
                'logistic': False,
                'tracking': True,
                'fleetrun': False,
                'status': "hibernate",
                'notify_offline': False,
            })
            r.message_post(body=body)
            self.create_device_log(r, body)

            # revisamos el tema de las suscripciones:
            default = dict(None or {})
            new_subscription = self.env['sale.subscription']

            if not subscription_hibernate_template_id:
                self.message_post(body="<b style='color:red'>AVISO</b>"
                                       "<br>No se pudo crear la subscripción de Hibernación automáticamente en el equipo."
                                       "<br>Deberá crearla manualmente."
                                       "<br>Es probable que ninguna plantilla de subscripción esta activa.")
            else:
                n = new_subscription.create({
                    'name': 'New Subscription',
                    'code': 'Hibernación ' + r.name,
                    'stage_id': subscription_hibernate_stage_id,
                    'template_id': subscription_hibernate_template_id,
                    'pricelist_id': hibernate_price_list_id,
                    'partner_id': r.client_id.id,
                    'gpsdevice_id': r.id,
                    'user_id': hibernate_user_id,
                    'team_id': hibernation_commercial_id,
                    'recurring_invoice_line_ids': [(0, _, {
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
        subscriptions = self.env['sale.subscription'].search([
            ['gpsdevice_id', 'in', active_records.ids],
            ['id', 'not in', skip_subscription_ids],
            ['stage_id', '!=', subscription_close_stage.id],
        ])

        # Alterando las suscripciones
        if subscriptions:
            self._change_subscriptions_stage(
                subscriptions,
                "El equipo se ha procesado como Hibernado en el sistema.",
                subscription_current_hibernate_stage_id
            )

        #Log Channel
        channel_msn = '<br/>Los equipos mencionados a continuación se procesaron para ser hibernados por motivo de:<br/>'
        channel_msn += self.comment + '<br/> soliciato por: ' + self.requested_by + '<br/>'
        channel_msn += self.devices_list

        # Send Message
        self.log_to_channel(channel_id, channel_msn)

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
        operation_log_comment = 'El equipo <strong>REEMPLAZADO</strong> se reemplaza con el equipo '
        operation_log_comment += '<strong>EQUIPO</strong> con número de ODT <strong>RELATED_ODT</strong>. <br/>'
        operation_log_comment += 'El equipo pasa a propiedad de la empresa.<br/>'
        operation_log_comment += 'Se entrega equipo a Soporte para revisión.<br/><br/>Comentario: ' + self.comment
        operation_log_comment_device = 'Se coloca <strong>REEMPLAZADO</strong> como reemplazo para <strong>EQUIPO</strong> '
        operation_log_comment_device += 'con la ODT <strong>RELATED_ODT</strong><br/><br/>Comentario: ' + self.comment

        for device in active_records:
            if not device.warranty_start_date:
                raise UserError(_(
                    'The device does not have Warranty Start Date.\n'
                    'Complete this first in order to process the Replacement Operation.'))

            # Preparando Datos para la suscripcion
            product_id = device.product_id
            serialnumber_id = device.serialnumber_id
            client_id = self.env.user.company_id
            device_current_client = device.client_id
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
                self._change_subscriptions_stage(subscription_to_close, repair_internal_notes)

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
                            'name': 'Reemplazo ' + self.destination_gpsdevice_ids.name,
                            'code': 'Reemplazo ' + self.destination_gpsdevice_ids.name,
                            'stage_id': subscription_in_progress_stage.id,
                            'gpsdevice_id': self.destination_gpsdevice_ids.id,
                        })

                        #_logger.warning('subscription_copy: %s', subscription_copy)
                        s.write({'stage_id': subscription_close_stage.id})
                    else:
                        operation_log_comment_device += '<p style="color:red">La suscripción ' + s.code
                        operation_log_comment_device += ' de el equipo reemplazado ' + device.name
                        operation_log_comment_device += ' tiene el estatus de ' + s.stage_id.name + '</p>'
            else:
                operation_log_comment_device += '<p style="color:red">El equipo reemplazado '
                operation_log_comment_device += device.name + ' no tiene suscripciones.</p>'

            operation_log_comment_device = operation_log_comment_device.replace('EQUIPO', device.name)
            operation_log_comment_device = operation_log_comment_device.replace('REEMPLAZADO', self.destination_gpsdevice_ids.name)
            operation_log_comment_device = operation_log_comment_device.replace('RELATED_ODT', self.related_odt.name)

            # Estatus del Equipo como desinstalado
            device.write({
                'status': "uninstalled",
                "client_id": self.env.user.company_id.id,
                'notify_offline': False,
            })

            device.message_post(body=operation_log_comment)

            self.create_device_log(device, operation_log_comment)
            self.log_to_channel(channel_id, operation_log_comment)

            self.destination_gpsdevice_ids.write({
                'warranty_start_date': device.warranty_start_date,
                'client_id': device_current_client.id,
                'status': 'replacement',
                'notify_offline': True,
            })

            operation_log_comment_device += '<br/>Fecha de garantía de <strong>'
            operation_log_comment_device += self.destination_gpsdevice_ids.warranty_start_date.strftime('%Y-%m-%d')
            operation_log_comment_device += '</strong> a <strong>'
            operation_log_comment_device +=self.destination_gpsdevice_ids.warranty_end_date.strftime('%Y-%m-%d') + '</strong>'

            self.destination_gpsdevice_ids.message_post(body=operation_log_comment_device)

        return {}

    def execute_substitution(self):
        # Check mandatory fields
        self._check_mandatory_fields(['comment', 'related_odt'])

        lgps_config = self.sudo().env['ir.config_parameter']
        channel_id = lgps_config.get_param('lgps.device_wizard.substitution_default_channel')
        if not channel_id:
            raise UserError(_(
                'There is not configuration for default channel.\n '
                'Configure this in order to send the notification.'
            ))

        # Obtenemos los Ids seleccionados
        active_model = self._context.get('active_model')
        active_records = self.env[active_model].browse(self._context.get('active_ids'))
        subscription_close_stage = self.sudo().env.ref('sale_subscription.sale_subscription_stage_closed')
        subscription_in_progress_stage = self.sudo().env.ref('sale_subscription.sale_subscription_stage_in_progress')

        # Messages to Log on Models
        repair_internal_notes = 'El equipo SUSTITUIDO se sustituyó con el equipo: EQUIPO con la ODT: RELATED_ODT'
        operation_log_comment = 'El equipo <strong>SUSTITUIDO</strong> se retira mientras que esta en revisión con ODT'
        operation_log_comment +=' <strong>RMA_ODT</strong>. Se instala el equipo: <strong>EQUIPO</strong> en su lugar'
        operation_log_comment +=' con la ODT <strong>RELATED_ODT</strong>. <br/>'
        operation_log_comment +='Se entrega equipo a Soporte para revisión.'
        operation_log_comment_device = 'Se coloca <strong>SUSTITUIDO</strong> como sustituto de <strong>EQUIPO</strong>  mientras está en '
        operation_log_comment_device +='revisión con la ODT <strong>RMA_ODT</strong><br/><br/> '
        operation_log_comment_device += 'Comentario: ' + self.comment

        for device in active_records:
            if not device.warranty_start_date:
                raise UserError(_(
                    'The device does not have Warranty Start Date. \n'
                    'Complete this first in order to process the Substitution Operation.'
                ))

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
                self._change_subscriptions_stage(subscription_to_close, repair_internal_notes)

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
                        operation_log_comment_device += '<p style="color:red">La suscripción ' + s.code
                        operation_log_comment_device += ' de el equipo sustituido ' + device.name
                        operation_log_comment_device += ' tiene el estatus de ' + s.stage_id.name + '</p>'
            else:
                operation_log_comment_device += '<p style="color:red">El equipo sustituido '
                operation_log_comment_device += device.name + ' no tiene suscripciones.</p>'

            # Estatus del Equipo como desinstalado
            device.write({'status': "uninstalled"})
            device.message_post(body=operation_log_comment)

            operation_log_comment_device = operation_log_comment_device.replace('EQUIPO', device.name)
            operation_log_comment_device = operation_log_comment_device.replace('SUSTITUIDO', self.destination_gpsdevice_ids.name)
            operation_log_comment_device = operation_log_comment_device.replace('RMA_ODT', nodt.name)
            self.destination_gpsdevice_ids.write({
                'status': "borrowed",
                'client_id': client_id.id,
            })
            self.destination_gpsdevice_ids.message_post(body=operation_log_comment_device)
            self.create_device_log(device, operation_log_comment)
            self.log_to_channel(channel_id, operation_log_comment)

        return {}

    def execute_wakeup(self):
        body = ''
        notify_gps_list = ''


        active_records = self.return_active_records()
        self.chek_status_before_further_process(active_records, 'hibernate')

        # LGPS Global Configuration
        lgps_config = self.sudo().env['ir.config_parameter']

        subscription_hibernate_stage_id = lgps_config.get_param(
            'lgps.device_wizard.hibernate_current_subscription_stage')
        if not subscription_hibernate_stage_id:
            raise UserError(_(
                'There is not configuration for default current subscriptions stage.\n'
                'Configure this in order to send the notification.'))

        channel_id = lgps_config.get_param('lgps.hibernate_device_wizard.default_channel')
        if not channel_id:
            raise UserError(_(
                'There is not configuration for default channel.\n Configure this in order to send the notification.'))

        subscription_in_progress_stage = self.sudo().env.ref('sale_subscription.sale_subscription_stage_in_progress')
        subscription_hibernate_stage_id = self.sudo().env['sale.subscription.stage'].search([
            ('id', '=', subscription_hibernate_stage_id)], limit=1)


        # Procesamos los quipos seleccionados:
        for r in active_records:
            acumulador = ""
            body = "[Proceso de Deshibernación]<br/><br/>" + self.comment + '<br/>'
            body += '<br/><b>Solicitado por</b>: '
            body += self.requested_by + '<br/>'
            gps_functions_summary = "<hr/>Se activan las funciones de:<br/><br/>"
            additional_functions = False

            platform = r.platform if r.platform else 'Sin Plataforma'
            client = r.client_id.name if r.client_id else 'Sin Cliente'
            equipo = r.name
            nick = r.nick if r.nick else 'NA'

            acumulador += '<br/><b>Plataforma:</b> ' + platform
            acumulador += '<br/><b>Cliente:</b> ' + client
            acumulador += '<br/><b>Solicitado Por:</b> ' + self.requested_by
            acumulador += '<br/><b>Equipo:</b> ' + equipo
            acumulador += '<br/><b>Nick:</b> ' + nick
            notify_gps_list += '<br/>' + client + ' || ' + equipo + ' || ' + nick + ' || ' + platform


            if self.tracking:
                additional_functions = True
                gps_functions_summary += "Rastreo<br/>"
            if self.fuel:
                additional_functions = True
                gps_functions_summary += "Combustible<br/>"
            if self.scanner:
                additional_functions = True
                gps_functions_summary += "Escánner<br/>"
            if self.temperature:
                additional_functions = True
                gps_functions_summary += "Temperatura<br/>"
            if self.logistic:
                additional_functions = True
                gps_functions_summary += "Logística<br/>"
            if self.fleetrun:
                additional_functions = True
                gps_functions_summary += "Mantenimiento de Flotilla<br/>"

            body += '<br/>' + acumulador
            if additional_functions:
                body += gps_functions_summary

            # Activando el equipo
            r.write({
                'fuel': self.fuel if self.fuel else r.fuel,
                'scanner': self.scanner if self.scanner else r.scanner,
                'temperature': self.temperature if self.temperature else r.temperature,
                'logistic': self.logistic if self.logistic else r.logistic,
                'tracking': self.tracking if self.tracking else r.tracking,
                'fleetrun': self.fleetrun if self.fleetrun else r.fleetrun,
                'status': self.device_status,
                'notify_offline': True,
            })
            # write Comment
            r.message_post(body=body)

            # Suscripciones

            # Buscamos las suscripciones que estén en el estatus marcado para hibernación y las pasamos a progreso
            hibernated_subscriptions = self.env['sale.subscription'].search([
                ['gpsdevice_id', '=', r.id],
                ['stage_id', '=', subscription_hibernate_stage_id.id]
            ])
            _logger.warning('subscription_hibernate_stage_id: %s', subscription_hibernate_stage_id)
            _logger.warning('hibernated_subscriptions: %s', hibernated_subscriptions)

            # Buscamos la suscripción que este en progreso y la pasamos a cerrada
            in_progress_subscriptions = self.env['sale.subscription'].search([
                ['gpsdevice_id', '=', r.id],
                ['stage_id', '=', subscription_in_progress_stage.id]
            ])

            _logger.warning('in_progress_subscriptions: %s', in_progress_subscriptions)

            if in_progress_subscriptions:
                self._change_subscriptions_stage(in_progress_subscriptions, "El equipo se ha deshibernado en el sistema.")

            if hibernated_subscriptions:
                self._change_subscriptions_stage(
                    subscriptions=hibernated_subscriptions,
                    comment="Se reactiva la suscripción por que el equipo fue deshibernado en el sistema",
                    default_stage=subscription_in_progress_stage
                )

            # Create Object Log
            self.create_device_log(r, body)

        channel_msn = '<br/>Los equipos mencionados a continuación se procesaron para ser deshibernados por motivo de:<br/>'
        channel_msn += self.comment + '<br/> soliciato por: ' + self.requested_by + '<br/>'
        channel_msn += notify_gps_list

        self.log_to_channel(channel_id, channel_msn)

        return {}

    def execute_add_reactivate(self):
        body = ''
        notify_gps_list = ''
        active_records = self.return_active_records()

        # LGPS Global Configuration
        lgps_config = self.sudo().env['ir.config_parameter']

        channel_id = lgps_config.get_param('lgps.add_reactivation_device_wizard.default_channel')
        if not channel_id:
            raise UserError(_(
                'There is not configuration for default channel.\n Configure this in order to send the notification.'))

        for r in active_records:
            acumulador = ""
            body = "[Proceso de Alta/Reactivación]<br/><br/>" + self.comment + '<br/>'
            gps_functions_summary = "<hr/>Se activan las funciones de:<br/><br/>"
            additional_functions = False
            reactivation_reason = dict(self._fields['reactivation_reason']._description_selection(self.env)).get(self.reactivation_reason)

            platform = self.platform if self.platform else 'Sin Plataforma'
            client = r.client_id.name if r.client_id else 'Sin Cliente'
            equipo = r.name
            nick = r.nick if r.nick else 'NA'

            acumulador += '<br/><b>Plataforma:</b> ' + platform
            acumulador += '<br/><b>Cliente:</b> ' + client
            acumulador += '<br/><b>Solicitado Por:</b> ' + self.requested_by
            acumulador += '<br/><b>Motivo:</b> ' + reactivation_reason
            acumulador += '<br/><b>Equipo:</b> ' + equipo
            #acumulador += '<br/><b>Nick:</b> ' + nick
            if self.cellchip_id:
                acumulador += '<br/><b>Línea Asignada:</b> ' + self.cellchip_id.name

            notify_gps_list += '<br/>' + client + ' || ' + equipo + ' || ' + nick + ' || ' + platform
            if self.tracking:
                additional_functions = True
                gps_functions_summary += "Rastreo<br/>"
            if self.fuel:
                additional_functions = True
                gps_functions_summary += "Combustible<br/>"
            if self.scanner:
                additional_functions = True
                gps_functions_summary += "Escánner<br/>"
            if self.temperature:
                additional_functions = True
                gps_functions_summary += "Temperatura<br/>"
            if self.logistic:
                additional_functions = True
                gps_functions_summary += "Logística<br/>"
            if self.fleetrun:
                additional_functions = True
                gps_functions_summary += "Mantenimiento de Flotilla<br/>"

            body += '<br/>' + acumulador
            if additional_functions:
                body += gps_functions_summary

            # Activando el equipo
            r.write({
                'fuel': self.fuel if self.fuel else r.fuel,
                'scanner': self.scanner if self.scanner else r.scanner,
                'temperature': self.temperature if self.temperature else r.temperature,
                'logistic': self.logistic if self.logistic else r.logistic,
                'tracking': self.tracking if self.tracking else r.tracking,
                'fleetrun': self.fleetrun if self.fleetrun else r.fleetrun,
                'platform': self.platform,
                'cellchip_id': self.cellchip_id.id if self.cellchip_id else None
            })
            # write Comment
            r.message_post(body=body)
            self.create_device_log(r, body)

            channel_msn = '<br/>Los equipos mencionados a continuación se procesaron para Alta/Reactivación por motivo de:<br/>'
            channel_msn += self.comment + '<br/> soliciato por: ' + self.requested_by + '<br/>'
            channel_msn += notify_gps_list

            self.log_to_channel(channel_id, channel_msn)

        return {}

    def execute_loan_substitution(self):

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

        repair_internal_notes = 'El equipo REEMPLAZADO se cambia por servicio en comodato con el equipo: '
        repair_internal_notes += 'EQUIPO en la ODT: RELATED_ODT'

        operation_log_comment = 'El equipo <strong>REEMPLAZADO</strong> se cambia por servicio en comodato con el  '
        operation_log_comment += 'equipo <strong>EQUIPO</strong> con número de ODT <strong>RELATED_ODT</strong>. <br/>'
        operation_log_comment += 'Se entrega equipo a Soporte para revisión.<br/><br/>Comentario: ' + self.comment

        operation_log_comment_device = 'Se coloca <strong>REEMPLAZADO</strong> como cambio de servicio en comodato para '
        operation_log_comment_device += ' <strong>EQUIPO</strong> con la ODT <strong>RELATED_ODT</strong><br/><br/>'
        operation_log_comment_device += 'Comentario: ' + self.comment

        for device in active_records:
            if device.status != "comodato":
                raise UserError(_(
                    'The device does not have status COMODATO.\n'
                    'Choose the right device or make sure the device status is correct to proceed.'))

            # Preparando Datos para la suscripcion
            product_id = device.product_id
            serialnumber_id = device.serialnumber_id
            client_id = self.env.user.company_id
            device_current_client = device.client_id
            device_id = device.id

            repair_internal_notes = repair_internal_notes.replace("REEMPLAZADO", device.name)
            repair_internal_notes = repair_internal_notes.replace("EQUIPO", self.destination_gpsdevice_ids.name)
            repair_internal_notes = repair_internal_notes.replace("RELATED_ODT", self.related_odt.name)

            # Cerramos las Suscripciones del equipo que sustituye
            subscription_to_close = self.destination_gpsdevice_ids.suscription_id
            if subscription_to_close:
                self._change_subscriptions_stage(subscription_to_close, repair_internal_notes)

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


                        subscription_copy = self.copy_subscription(s, {
                            'name': 'Reemplazo ' + self.destination_gpsdevice_ids.name,
                            'code': 'Reemplazo ' + self.destination_gpsdevice_ids.name,
                            'stage_id': subscription_in_progress_stage.id,
                            'gpsdevice_id': self.destination_gpsdevice_ids.id,
                        })

                        #_logger.warning('subscription_copy: %s', subscription_copy)
                        s.write({'stage_id': subscription_close_stage.id})
                    else:
                        operation_log_comment_device += '<p style="color:red">La suscripción ' + s.code
                        operation_log_comment_device += ' de el equipo reemplazado ' + device.name
                        operation_log_comment_device += ' tiene el estatus de ' + s.stage_id.name + '</p>'
            else:
                operation_log_comment_device += '<p style="color:red">El equipo reemplazado '
                operation_log_comment_device += device.name + ' no tiene suscripciones.</p>'

            operation_log_comment_device = operation_log_comment_device.replace('EQUIPO', device.name)
            operation_log_comment_device = operation_log_comment_device.replace('REEMPLAZADO', self.destination_gpsdevice_ids.name)
            operation_log_comment_device = operation_log_comment_device.replace('RELATED_ODT', self.related_odt.name)

            # Estatus del Equipo como desinstalado
            device.write({
                'status': "uninstalled",
                "client_id": self.env.user.company_id.id,
                'notify_offline': False,
            })

            device.message_post(body=operation_log_comment)

            self.create_device_log(device, operation_log_comment)
            self.log_to_channel(channel_id, operation_log_comment)

            self.destination_gpsdevice_ids.write({
                'client_id': device_current_client.id,
                'status': 'comodato',
                'notify_offline': True,
            })

            self.destination_gpsdevice_ids.message_post(body=operation_log_comment_device)

        return {}

    def return_active_records(self):
        active_model = self._context.get('active_model')
        active_records = self.env[active_model].browse(self._context.get('active_ids'))

        return active_records

    def chek_status_before_further_process(self, devices, status):
        error = False
        buffer =''
        #row_list = []

        for device in devices:
            if device.status != status or device.platform == 'Drop':
                error = True
                buffer += device.name + '  /  ' + device.status + '  /  ' + device.platform + '\n'
                #row_list.append([device.name, device.nick, device.status])

        if error:
            #_logger.warning('row_list: %s', row_list)
            raise UserError(
                #_('Some devices does not has the right status for this operation.\n\n ' + self.cool_format(row_list))
                _('Some devices does not has the right status for this operation.\n\n ' + buffer)
            )

        return {}

    def get_price_from_pricelist(self, price_list, product):
        lista_de_precios = self.sudo().env['product.pricelist'].search([('id', '=', price_list)], limit=1)
        if lista_de_precios:
            precio_de_lista = lista_de_precios.get_product_price(product, 1, False)
            if precio_de_lista:
                price = precio_de_lista
            else:
                price = 0
        else:
            price = product.lst_price

        return price

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

    def _change_subscriptions_stage(self, subscriptions, comment=None, default_stage=None):
        close = False

        if not default_stage:
            close = True
            subscription_close_stage = self.sudo().env.ref('sale_subscription.sale_subscription_stage_closed')
        else:
            if isinstance(default_stage, str):
                subscription_close_stage = self.sudo().env['sale.subscription.stage'].search([
                    ('id', '=', default_stage)], limit=1)
            else:
                subscription_close_stage = default_stage

        for subscription in subscriptions:
            subscription.write({'stage_id': subscription_close_stage.id})
            if close:
                if comment:
                    body = 'Se cierra suscripción por motivo de: <br>' + comment
                else:
                    body = 'Se cierra suscripción por motivo de: <br>'
            else:
                body = comment

            subscription.message_post(body=body)

        return True

    def create_device_log(self, device, log_comment=""):
        log_object = self.env['lgps.device_history']

        dictionary = {
            'name': device.name + ' - ' + self.operation_mode,
            'product_id': device.product_id.id,
            'serialnumber_id': device.serialnumber_id.id,
            'client_id': device.client_id.id,
            'gpsdevice_ids': device.id,
            'destination_gpsdevice_ids': self.destination_gpsdevice_ids.id,
            'operation_mode': self.operation_mode,
            'related_odt': self.related_odt.id,
            'requested_by': self.requested_by,
            'comment': self.comment,
            'reason': self.reason,
            'log_msn': log_comment
        }
        device_log = log_object.create(dictionary)
        return device_log

    def log_to_channel(self, channel_id, channel_msn):

        if not channel_id:
           raise UserError(
               _('There is not configuration for default channel.\n Configure this in order to send the notification.')
           )
        else:
            channel_notifier = self.sudo().env['mail.channel'].search([('id', '=', channel_id)])
            channel_notifier.message_post(body=channel_msn, subtype='mail.mt_comment', partner_ids=[(4, self.env.uid)])

        return {}

    def cool_format(self, data):
        buffer = ''
        col_width = max(len(word) for row in data for word in row) + 4  # padding
        for row in data:
            buffer += "".join(word.ljust(col_width) for word in row) + '\n'
        _logger.warning('buffer: %s', buffer)

        return buffer
