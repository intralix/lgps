from odoo import api, models, fields, _
from odoo.exceptions import UserError, ValidationError

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
            ('comodatos', _('Comodato Service')),
            ('other', _('Other')),
            ('reinstallation', _('Reinstallation')),
            ('uninstallation', _('Uninstallation'))
        ],
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

        if self.name.startswith('ODT'):
            # Determinamos si parece una garantía
            if self.odt_type == 'service' and self.invoice_method == 'none':
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
        return
