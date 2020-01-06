from odoo import api, models, fields, _

class FailureStage(models.Model):
    _name = 'lgps.failure.stages'
    _description = 'Failure Stage'
    _order = 'sequence,name'

    name = fields.Char()
    sequence = fields.Integer(default=10)
    fold = fields.Boolean()
    active = fields.Boolean(default=True)
    state = fields.Selection(
        [
            ('reported_failure', _('Falla reportada')),
            ('for_attending', _('Por atender')),
            ('attended', _('Atendida'))
        ],
        default='reported_failure',
    )
