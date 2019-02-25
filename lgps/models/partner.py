from odoo import api, models, fields


class Partner(models.Model):
    _inherit = 'res.partner'

    # Filtrar aquellos que no han sido seleccionados o le pertenecen al cliente Principal (LGPS)
    gpsdevice_ids = fields.One2many(
        comodel_name="lgps.gpsdevice",
        inverse_name="client_id",
        string="Gps Devices",
        readonly=True,
    )

    first_installation_day = fields.Date(
        string="First Installation Day"
    )

    client_type = fields.Selection(
        [
            ('new', _('New')),
            ('existent', _('Existent')),
        ],
        default='new',
        string="Client Type"
    )
