from odoo import api, models, fields, _
from odoo.exceptions import UserError, ValidationError
import logging
_logger = logging.getLogger(__name__)


class Odt(models.Model):
    _inherit = 'repair.order'

    create_date = fields.Datetime(
        'Creation Date',
        readonly=True
    )

    gpsdevice_id = fields.Many2one(
        comodel_name="lgps.gpsdevice",
        string=_("Gps Device"),
        ondelete="set null",
        index=True,
    )

    installer_id = fields.Many2one(
        comodel_name="hr.employee",
        string=_("Installer"),
    )

    assistant_a_id = fields.Many2one(
        comodel_name="hr.employee",
        string=_("Assistant A"),
    )

    assistant_b_id = fields.Many2one(
        comodel_name="hr.employee",
        string=_("Assistant B"),
    )

    service_date = fields.Date(
        default=fields.Date.today,
        string=_("Service Date"),
    )

    closed_date = fields.Date(
        string=_("Closed Date"),
    )

    odt_type = fields.Selection(
        [
            ('service', _('Service')),
            ('new_installation', _('New Installation')),
            ('reinstallation', _('Reinstallation')),
            ('uninstallation', _('Uninstallation'))
        ],
        default="service",
        required=True,
    )

    days_count = fields.Integer(
        compute='_compute_days_count',
        store=True,
        string=_("Open Days"),
    )

    is_guarantee = fields.Boolean(
        default=False,
        string=_("It is a guarantee"),
        track_visibility='onchange',
    )

    authorization_requested = fields.Boolean(
        default=False,
        string=_("Authorization requested"),
    )

    authorized_warranty = fields.Selection(
        [
            ('na', _('No requested')),
            ('waiting', _('Waiting for resolution')),
            ('authorized', _('Authorized')),
            ('rejected', _('Rejected')),
        ],
        default="na",
    )

    odt_branch_office = fields.Selection(
        [
            ('s1', _('Guadalajara')),
            ('s2', _('Querétaro')),
            ('s3', _('México')),
            ('s4', _('Córdoba')),
        ],
        default="s1",
        required=True,
    )

    time_spent = fields.Float(
        string=_("Time Spent"),
        help='Time spent in solution to this record',
        track_visibility='onchange'
    )

    authorizations_count = fields.Integer(
        string=_("Authorizations Count"),
    )

    guarantee_type = fields.Selection(
        [
            ('manpower_warranty', _('Garantía de mano de obra')),
            ('product warranty', _('Garantía de producto')),
            ('all_warranty', _('Ambas')),
        ],
        string=_("Guarantee Type"),
        track_visibility='onchange',
    )

    stock_out_id = fields.Many2one(
        comodel_name="stock.picking",
        string=_("Stock Out"),
    )

    stock_in_id = fields.Many2one(
        comodel_name="stock.picking",
        string=_("Stock In"),
    )

    initial_photos = fields.Boolean(
        default=False,
        string=_("Initial photos"),
        track_visibility='onchange',
    )

    end_photos = fields.Boolean(
        default=False,
        string=_("End Photos"),
        track_visibility='onchange',
    )

    tests_run = fields.Boolean(
        default=False,
        string=_("Tests run"),
        track_visibility='onchange',
    )

    related_invoice = fields.Many2one(
        comodel_name="account.invoice",
        string=_("Related Invoice"),
        ondelete="set null"
    )

    check_status = fields.Selection(
        [
            ('finished_and_authorized', _('Terminado / Autorizado (FTQ)')),
            ('finished_and_corrected', _('Terminado / Corregido')),
            ('incomplete', _('Incompleto')),
        ],
        string=_("Estatus Calidad"),
        track_visibility='onchange',
    )

    check_comment = fields.Text(
        string=_("Check Comment")
    )

    cancel_reason = fields.Selection(
        [
            ('unit_in_repair', _('Unidad en taller')),
            ('unit_wrecked', _('Unidad siniestrada')),
            ('unit_did_not_arrive', _('No llegó la unidad')),
            ('unit_leaves', _('Se retira unidad')),
            ('other', _('Otro')),
        ],
        string=_("Cancelation Reason")
    )

    cancel_other_reason = fields.Text(
        string=_("Other Reason")
    )

    applicant_deparment = fields.Selection(
        [
            ('operations', _('Operaciones')),
            ('afther_sales', _('Post Ventas')),
        ],
        default="operations",
        string=_("Applicant Department")
    )

    @api.one
    @api.depends('closed_date')
    def _compute_days_count(self):
        if self.closed_date and self.create_date:
            start_dt = fields.Date.from_string(self.create_date)
            end_today_dt = fields.Date.from_string(self.closed_date)
            difference = end_today_dt - start_dt
            time_difference_in_days = difference.days
            self.days_count = time_difference_in_days

    @api.model
    def create(self, values):
        # _logger.warning('Calling Created Method')
        new_record = super(Odt, self).create(values)

        service_date = fields.Date.from_string(values.get('service_date'))
        if not service_date:
            raise UserError(_("La ODT debe tener una fecha de servicio válida."))
        else:
            today = fields.Date.today()
            difference = today - service_date
            time_difference_in_days = difference.days

        if time_difference_in_days > 2:
            raise UserError(_("Por políticas de la empresa, no puedes dar de alta un servicio con fecha de servicio anterior a 2 días."))

        return new_record

    @api.multi
    def write(self, values):
        # _logger.warning('Calling Created Method')
        service_date = fields.Date.from_string(values.get('service_date'))

        if service_date:
            today = fields.Date.today()
            difference = today - service_date
            time_difference_in_days = difference.days

            if time_difference_in_days > 2:
                raise UserError(_("Por políticas de la empresa, no puedes dar de alta un servicio con fecha de servicio anterior a 2 días."))

        return super(Odt, self).write(values)

    def action_validate(self):
        self._check_rules()
        self._check_operations_rules()
        self.closed_date = fields.Date.today()
        odt_action_validate = super(Odt, self).action_validate()
        return odt_action_validate


    def _check_rules(self):
        warranty_was_void = False
        billable_odt_types = ['reinstallation', 'uninstallation']

        # Validamos que el registro es una ODT
        if self.name.startswith('ODT'):

            # ODT De Tipo Servicio
            if self.odt_type == 'service':
                self.validate_service_rules()
                self.check_warranty()

                # Si la ODT no es una instalación nueva, validamos que se cobre con su procedimiento de autorización
            if self.odt_type in billable_odt_types and self.invoice_method == 'none':
                if not self.is_guarantee:
                    raise UserError(
                        _("Repair seems to be a warranty.\n\nYou must check warranty checkbox")
                    )
                self.check_warranty()

        return

    def validate_service_rules(self):
        # Ensure Failures
        warranty_was_void = self.check_has_failures()
        # Check if need Warranty
        if self.invoice_method == 'none':
            if not warranty_was_void:
                if not self.is_guarantee:
                    raise UserError(
                        _("Repair seems to be a warranty.\n\nYou must check warranty checkbox")
                    )
        return

    def check_has_failures(self):
        needs_void_warranty = False
        msn_buff = ""

        # Revisamos si es un servicio, si lo es hay que revisar si tiene fallas asociadas
        if self.odt_type == 'service':
            # ¿Tiene fallas registradas?
            failures = self.env['lgps.failures'].search([('repairs_id', '=', self.id)])
            if not failures:
                raise UserError(
                    _("Each service ODT must have a failure record associated.\n\nCreate this record first.")
                )
            else:
                for f in failures:
                    _logger.warning('Failure: %s', f)
                    if f.manipulation_detected:
                        msn_buff += "[" + f.name + "] : " + f.failure_functionalities_list_id.name \
                                + " / " + f.failure_components_list_id.name \
                                + " / " + f.failure_root_problem_list_id.name + "\n"
                        needs_void_warranty = True

        if needs_void_warranty and self.invoice_method == 'none':
            raise UserError(_("Manipulation detected on:\n\n" + msn_buff +"\n\nThis service has to be invoiced."))

        return needs_void_warranty

    def check_warranty(self):
        if self.is_guarantee:
            if self.authorized_warranty == 'na':
                raise UserError(
                    _("Repair must be authorized before confirmation.\n\nYou must create an authorization request")
                )
            if self.authorized_warranty == 'waiting':
                raise UserError(
                    _("Repair has not been authorized.\n\nYou must wait for resolution to the previous request")
                )
            if self.authorized_warranty == 'rejected':
                raise UserError(
                    _("Repair was not authorized.\n\nYou must change the invoicing method for invoice this service")
                )
        return

    def void_warranty(self, string_reason):

        record = self
        record.write({
            'is_guarantee': True,
            'authorization_requested': True,
            'authorized_warranty': 'rejected',
        })

        operation_log_comment = "Esta ODT se marca como <strong style='color:red'>garantía no autorizada</strong>" \
                                " por las fallas encontradas:<br><br>"
        string_reason = string_reason.replace("\n", "<br>")
        operation_log_comment += string_reason

        record.message_post(body=operation_log_comment)

        return {}

    def _check_operations_rules(self):

        if self.operations:
            for operation in self.operations:
                found_error = False

                if operation.type == 'add':
                    if operation.location_id.name == 'Customers':
                        if operation.location_dest_id.name != 'Customers':
                            found_error = True
                    else:
                        pos = operation.location_id.name.find('Respaldo')
                        if pos < 0 or operation.location_dest_id.name != 'Customers':
                            found_error = True
                elif operation.type == 'remove':
                    if operation.location_id.name == 'Customers' and operation.location_dest_id.name == 'Customers':
                        found_error = False
                    else:
                        found_error = True

                if found_error:
                    raise UserError(
                        _('Verifica que las ubicaciones seleccionadas en tus piezas sean correctas.\n\n'
                          + operation.location_id.display_name + ' -> ' + operation.location_dest_id.display_name)
                    )
        return
