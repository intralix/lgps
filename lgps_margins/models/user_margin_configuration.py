from odoo import api, models, fields, _


class UserMarginConfigurations(models.Model):
    _inherit = ['res.users']

    min_margin = fields.Float(
        string=_("Min Margin"),
        digits=(2, 2),
        help=_('Min Margin expected for this user in Sales Orders')
    )

    skip_min_margin_rule = fields.Boolean(
        string=_("Skip Margin Rule"),
        default=False,
        help=_('Allow to sell with negative margin')
    )
