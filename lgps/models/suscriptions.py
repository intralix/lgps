from odoo import api, models, fields


class Suscription(models.Model):
    _inherit = 'sale.subscription'

    gpsdevice_id = fields.Many2one(
        comodel_name="lgps.gpsdevice",
        string="Gps Device",
    )

    grouper_type = fields.Selection(
        selection=[
            ("A", "A"),
            ("B", "B"),
            ("C", "C"),
            ("D", "D"),
            ("E", "E"),
        ],
        string="Grouper Type",
        default="A",
    )
