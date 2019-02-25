from odoo import api, models, fields

class Suscription(models.Model):
    _inherit = 'sale.subscription'

    gpsdevice_id = fields.Many2one(
        comodel_name="lgps.gpsdevice",
        string="Gps Device",
    )

    grouper_type = fields.Selection(
        selection=[
            (1, "A"),
            (2, "B"),
            (3, "C"),
            (4, "D"),
            (5, "E"),
        ],
        string="Grouper Type",
        default=1,
    )
