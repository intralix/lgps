from odoo import api, models, fields, _


class Ticket(models.Model):
    _inherit = 'helpdesk.ticket'

    gpsdevice_id = fields.Many2one(
        comodel_name="lgps.gpsdevice",
        string=_("Gps Device"),
        ondelete="set null",
        index=True,
    )
