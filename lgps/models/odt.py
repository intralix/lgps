from odoo import api, models, fields


class Odt(models.Model):
    _inherit = 'repair.order'

    gpsdevice_id = fields.Many2one(
        comodel_name="lgps.gpsdevice",
        string="Gps Device",
        ondelete="set null",
        index=True,
    )

    installer_id = fields.Many2one(
        comodel_name="hr.employee",
        string="Installer",
    )

    assistant_a_id = fields.Many2one(
        comodel_name="hr.employee",
        string="Assistant A",
    )

    assistant_b_id = fields.Many2one(
        comodel_name="hr.employee",
        string="Assistant B",
    )

    service_date = fields.Date(
        default=fields.Date.today,
        string="Service Date",
    )
