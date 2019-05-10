from odoo import api, models, fields, _

class Odt(models.Model):
    _inherit = 'repair.order'
    create_date = fields.Datetime('Creation Date', readonly=True),

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
