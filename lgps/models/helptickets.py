from odoo import api, models, fields


class Ticket(models.Model):
    _inherit = 'helpdesk.ticket'

    gpsdevice_id = fields.Many2one(
        comodel_name="lgps.gpsdevice",
        string="Gps Device",
        ondelete="set null",
        index=True,
    )
