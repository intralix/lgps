from odoo import api, models, fields, _

class FailureOdt(models.Model):
    _inherit = 'repair.order'

    failures_id = fields.Many2one(
        comodel_name="lgps.failures",
        string=_("Fallas"),
        ondelete="set null",
        index=True,
    )

