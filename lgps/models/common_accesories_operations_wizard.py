# -*- coding: utf-8 -*-
from datetime import timedelta
from odoo import api, models, fields, _
from odoo.exceptions import UserError
import logging, re


_logger = logging.getLogger(__name__)
TAG_RE = re.compile(r'<[^>]+>')

class CommonOperationsToAccessoriesWizard(models.TransientModel):
    _name = "lgps.common_operations_accessory_wizard"
    _description = "Common Operations To Accessories Wizard"



    def _default_accesories(self):
        return self.env['lgps.accessory'].browse(self._context.get('active_ids'))

    operation_mode = fields.Selection(
        [
            ('replacement', _('Reemplazo de accesorio')),
            ('substitution', _('Sustitución por revisión')),
        ],
        default='drop'
    )

    accessories_ids = fields.Many2many(
        comodel_name='lgps.accessory',
        string="Gps Device",
        required=True,
        default=_default_accesories,
    )

    destination_accessories_ids = fields.Many2one(
        comodel_name='lgps.accessory',
        string="Substitute equipment",
        domain="[('status', 'in', ['new', 'inventory', 'uninstalled', 'ready','backup']), ('gpsdevice_id', '=', False)]"
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

    accessory_list = fields.Text(
        string=_("Accessory List")
    )
    # Available services
    accesory_status = fields.Selection(
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
            ("ready", _("Ready to Install")),
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

    @api.multi
    def execute_operation(self):
        if len(self._context.get('active_ids')) < 1:
            raise UserError(_('Select at least one record.'))



        # Replacement
        if self.operation_mode == 'replacement':
            self.execute_replacement()
        # Substitution
        if self.operation_mode == 'substitution':
            self.execute_substitution()

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

        repair_internal_notes = 'El accesorio REEMPLAZADO / REEMPLAZADO_SERIE se reemplazó con el accesorio: EQUIPO / EQUIPO_SERIE en el equipo DEVICE '
        repair_internal_notes += 'con la ODT: RELATED_ODT debido a que está dentro de garantía.'

        operation_log_comment = 'El accesorio <strong>REEMPLAZADO / REEMPLAZADO_SERIE</strong> se reemplaza con el accesorio '
        operation_log_comment += '<strong>EQUIPO / EQUIPO_SERIE </strong> en el equipo DEVICE '
        operation_log_comment += 'con número de ODT <strong>RELATED_ODT</strong>. <br/>'
        operation_log_comment += 'El accesorio pasa a propiedad de la empresa.<br/>'
        operation_log_comment += 'Se entrega accesorio a Soporte para revisión.<br/><br/>Comentario: ' + self.comment
        operation_log_comment_accessory = 'Se coloca accesorio como reemplazo para el accesorio <strong>EQUIPO / EQUIPO_SERIE</strong> '
        operation_log_comment_accessory += 'en el equipo <strong>DEVICE</strong> con la ODT <strong>RELATED_ODT</strong>'
        operation_log_comment_accessory += ' por estar dentro de garantía.<br/><br/>'
        operation_log_comment_accessory += 'Comentario: ' + self.comment

        for accessory in active_records:
            # if not device.warranty_start_date:
            #    raise UserError(_(
            #       'The accessory does not have Warranty Start Date.\n'
            #       'Complete this first in order to process the Replacement Operation.'))

            # Preparando Datos para la suscripcion
            product_id = accessory.product_id
            serialnumber_id = accessory.serialnumber_id
            client_id = self.env.user.company_id
            device_id = accessory.gpsdevice_id
            gps_device = accessory.gpsdevice_id if accessory.gpsdevice_id else ''

            repair_internal_notes = repair_internal_notes.replace("REEMPLAZADO_SERIE", serialnumber_id.name or 'NA')
            repair_internal_notes = repair_internal_notes.replace("REEMPLAZADO", accessory.name)
            repair_internal_notes = repair_internal_notes.replace("EQUIPO_SERIE", self.destination_accessories_ids.serialnumber_id.name or 'NA')
            repair_internal_notes = repair_internal_notes.replace("EQUIPO", self.destination_accessories_ids.name)
            repair_internal_notes = repair_internal_notes.replace("RELATED_ODT", self.related_odt.name)
            repair_internal_notes = repair_internal_notes.replace("DEVICE", gps_device.name or 'NA')

            odt_name = self.env['ir.sequence'].sudo().next_by_code('repair.order')
            odt_name = odt_name.replace('ODT', 'RMA')

            odt_object = self.env['repair.order']
            dictionary = {
                'name': odt_name,
                'product_id': product_id.id,
                'product_qty': 1,
                'lot_id': serialnumber_id.id,
                'partner_id': client_id.id,
                'gpsdevice_id': False,
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

            operation_log_comment = operation_log_comment.replace("REEMPLAZADO_SERIE", serialnumber_id.name or 'NA')
            operation_log_comment = operation_log_comment.replace("REEMPLAZADO", accessory.name)
            operation_log_comment = operation_log_comment.replace('EQUIPO_SERIE', self.destination_accessories_ids.serialnumber_id.name or 'NA')
            operation_log_comment = operation_log_comment.replace('EQUIPO', self.destination_accessories_ids.name)
            operation_log_comment = operation_log_comment.replace('RELATED_ODT', self.related_odt.name)
            operation_log_comment = operation_log_comment.replace("DEVICE", gps_device.name)

            operation_log_comment_accessory = operation_log_comment_accessory.replace('EQUIPO_SERIE', serialnumber_id.name or 'NA')
            operation_log_comment_accessory = operation_log_comment_accessory.replace('EQUIPO', accessory.name)
            operation_log_comment_accessory = operation_log_comment_accessory.replace('RELATED_ODT', self.related_odt.name)
            operation_log_comment_accessory = operation_log_comment_accessory.replace("DEVICE", gps_device.name)
            #operation_log_comment_device += '<br/>Fecha de garantía de <strong>'
            #operation_log_comment_device += self.destination_accessories_ids.warranty_start_date.strftime('%Y-%m-%d')
            #operation_log_comment_device += '</strong> a <strong>'
            #operation_log_comment_device += device.warranty_start_date.strftime('%Y-%m-%d') + '</strong>'

            self.create_device_log(gps_device, accessory, operation_log_comment)
            self._complete_relations(gps_device, self.destination_accessories_ids)

            self.destination_accessories_ids.write({'installation_date': accessory.installation_date })

            # Estatus del Equipo como desinstalado
            accessory.write({
                'status': "uninstalled",
                "client_id": self.env.user.company_id.id,
                'gpsdevice_id': False,

            })
            accessory.message_post(body=operation_log_comment)

            self.create_accesory_log(accessory)
            self.log_to_channel(channel_id, operation_log_comment)

            #self.destination_accessories_ids.write({'warranty_start_date': accessory.warranty_start_date})
            self.destination_accessories_ids.message_post(body=operation_log_comment_accessory)

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

        # Messages to Log on Models
        repair_internal_notes = 'El accesorio SUSTITUIDO / SUSTITUIDO_SERIE se sustituyó con el accesorio: EQUIPO / EQUIPO_SERIE con la ODT: RELATED_ODT en el equipo DEVICE '
        operation_log_comment = 'El accesorio <strong>SUSTITUIDO / SUSTITUIDO_SERIE</strong> se retira mientras que esta en revisión con ODT'
        operation_log_comment += ' <strong>RMA_ODT</strong>. <br/>Se instala el accesorio: <strong>EQUIPO / EQUIPO_SERIE</strong> en su lugar'
        operation_log_comment += ' con la ODT <strong>RELATED_ODT</strong>. <br/>'
        operation_log_comment += 'Se entrega accesorio a Soporte para revisión.'
        operation_log_comment_device = 'Se coloca como sustituto al accesorio <strong>EQUIPO / EQUIPO_SERIE</strong>  mientras está en '
        operation_log_comment_device += 'revisión con la ODT <strong>RMA_ODT</strong><br/><br/> '
        operation_log_comment_device += 'Comentario: ' + self.comment

        # Obtenemos los Ids seleccionados
        active_model = self._context.get('active_model')
        active_records = self.env[active_model].browse(self._context.get('active_ids'))

        #Desasginar el dispositivo del GPS
        # Cambiar el estatus del accesorio a Desinstalado

        for accessory in active_records:
            # if not accessory.gpsdevice_id.warranty_start_date:
            #    raise UserError(_(
            #       'The gps device does not have Warranty Start Date. \n'
            #       'Complete this first in order to process the Substitution Operation.'
            #   ))

            # Preparando Datos para la ODT
            product_id = accessory.product_id
            serialnumber_id = accessory.serialnumber_id
            client_id = accessory.client_id
            gps_device = accessory.gpsdevice_id

            repair_internal_notes = repair_internal_notes.replace("SUSTITUIDO_SERIE", serialnumber_id.name)
            repair_internal_notes = repair_internal_notes.replace("SUSTITUIDO", accessory.name)
            repair_internal_notes = repair_internal_notes.replace("EQUIPO_SERIE", self.destination_accessories_ids.serialnumber_id.name)
            repair_internal_notes = repair_internal_notes.replace("EQUIPO", self.destination_accessories_ids.name)
            repair_internal_notes = repair_internal_notes.replace("DEVICE", gps_device.name)
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
                'gpsdevice_id': False,
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
            operation_log_comment = operation_log_comment.replace("SUSTITUIDO_SERIE", serialnumber_id.name or 'NA')
            operation_log_comment = operation_log_comment.replace("SUSTITUIDO", accessory.name)
            operation_log_comment = operation_log_comment.replace('EQUIPO_SERIE', self.destination_accessories_ids.serialnumber_id.name or 'NA')
            operation_log_comment = operation_log_comment.replace('EQUIPO', self.destination_accessories_ids.name)
            operation_log_comment = operation_log_comment.replace('RELATED_ODT', self.related_odt.name)

            # Estatus del Equipo como desinstalado
            self.destination_accessories_ids.write({'installation_date': accessory.installation_date})
            self.create_device_log(gps_device, accessory, operation_log_comment)
            self._complete_relations(gps_device, self.destination_accessories_ids)

            accessory.write({
                'status': "uninstalled",
                'gpsdevice_id': False
            })
            accessory.message_post(body=operation_log_comment)

            operation_log_comment_device = operation_log_comment_device.replace('EQUIPO_SERIE', serialnumber_id.name or 'NA')
            operation_log_comment_device = operation_log_comment_device.replace('EQUIPO', accessory.name)
            operation_log_comment_device = operation_log_comment_device.replace('RMA_ODT', nodt.name)
            self.destination_accessories_ids.write({'status': "borrowed"})
            self.destination_accessories_ids.message_post(body=operation_log_comment_device)
            self.create_accesory_log(accessory)
            self.log_to_channel(channel_id, operation_log_comment)

        return {}

    def return_active_records(self):
        active_model = self._context.get('active_model')
        active_records = self.env[active_model].browse(self._context.get('active_ids'))

        return active_records

    def chek_status_before_further_process(self, accessories, status):
        error = False
        buffer = ''
        # row_list = []

        for accessory in accessories:
            if accessory.status != status or accessory.platform == 'Drop':
                error = True
                buffer += accessory.name + '  /  ' + accessory.status + '  /  ' + accessory.serialnumber_id.name + '\n'

        if error:
            # _logger.warning('row_list: %s', row_list)
            raise UserError(
                # _('Some devices does not has the right status for this operation.\n\n ' + self.cool_format(row_list))
                _('Some accessories does not has the right status for this operation.\n\n ' + buffer)
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

    def create_device_log(self, device, accessory, comment):
        log_object = self.env['lgps.device_history']
        operation_executed = 'acc' + self.operation_mode
        comment = TAG_RE.sub('', comment)

        dictionary = {
            'name': device.name + ' - ' + operation_executed,
            'product_id': device.product_id.id,
            'serialnumber_id': accessory.serialnumber_id.id,
            'client_id': device.client_id.id,
            'gpsdevice_ids': device.id,
            'destination_gpsdevice_ids': False,
            'operation_mode': operation_executed,
            'related_odt': self.related_odt.id,
            'requested_by': self.requested_by,
            'comment': comment+self.comment
        }
        device_log = log_object.create(dictionary)
        return device_log

    def create_accesory_log(self, accessory):
        log_object = self.env['lgps.accessory_history']

        dictionary = {
            'name': accessory.name + ' - ' + self.operation_mode,
            'product_id': accessory.product_id.id,
            'serialnumber_id': accessory.serialnumber_id.id,
            'client_id': accessory.client_id.id,
            'accessory_ids': accessory.id,
            'destination_accessory_ids': self.destination_accessories_ids.id,
            'operation_mode': self.operation_mode,
            'related_odt': self.related_odt.id,
            'requested_by': self.requested_by,
            'comment': self.comment
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

    def _complete_relations(self, device, accessory):
        accessory.write({
            'gpsdevice_id': device.id
        })

        device.accessory_ids = [(4, accessory.id, 0)]
        return
