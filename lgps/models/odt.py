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
        ],
        default="s1",
        required=True,
    )

    time_spent = fields.Float(
        string=_("Time Spent"),
        help='Time spent in solution to this record',
        track_visibility='onchange'
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

    def action_validate(self):
        self._check_rules()
        self.closed_date = fields.Date.today()
        odt_action_validate = super(Odt, self).action_validate()
        return odt_action_validate

    def _check_rules(self):
        warranty_was_void = False
        # Validamos que el registro es una ODT
        if self.name.startswith('ODT'):
            # ¿Es un servicio?
            if self.odt_type == 'service' and self.invoice_method == 'none':
                warranty_was_void = self.check_has_failures()
                if not warranty_was_void:
                    if not self.is_guarantee:
                        raise UserError(
                            _("Repair seems to be a warranty.\n\nYou must check warranty checkbox")
                        )

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
                        #Check for Failures
                        #values = self.env['lgps.failures'].search([('id', 'in', self.failures_ids)])
        return

    def check_has_failures(self):
        # ¿Tiene fallas registradas?
        failures = self.env['lgps.failures'].search([('repairs_id', '=', self.id)])
        if not failures:
            raise UserError(
                _("Each service ODT must have a failure record associated.\n\nCreate this record first.")
            )
        else:
            needs_void_warranty = False
            msn_buff = ""
            for f in failures:
                _logger.warning('Failure: %s', f)
                if f.manipulation_detected:
                    msn_buff += "[" + f.name + "] : " + f.failure_functionalities_list_id.name \
                                + " / " + f.failure_components_list_id.name \
                                + " / " + f.failure_root_problem_list_id.name + "\n"
                    needs_void_warranty = True

            if needs_void_warranty:
                # self.void_warranty(msn_buff)
                raise UserError(_("Manipulation detected on:\n\n" + msn_buff +"\n\nThis service has to be invoiced."))

        return needs_void_warranty

    def void_warranty(self, string_reason):

        record = self
        record.write({
            'is_guarantee': True,
            'authorization_requested': True,
            'authorized_warranty': 'rejected',
        })

        operation_log_comment = "Esta ODT se marca como <strong style='color:red'>garantía no autorizada</strong> por las fallas encontradas:<br><br>"
        string_reason = string_reason.replace("\n", "<br>")
        operation_log_comment += string_reason

        record.message_post(body=operation_log_comment)

        return {}
