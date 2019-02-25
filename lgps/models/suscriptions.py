from odoo import api, models, fields

class Suscription(models.Model):
    _inherit = 'sale.subscription'

    gpsdevice_id = fields.Many2one(
        comodel_name="lgps.gpsdevice",
        string="Gps Device",
    )
