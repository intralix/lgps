from odoo import api, models, fields, _

class Lead(models.Model):
    _inherit = 'crm.lead'

    weighted_amount = fields.Integer(string="Weighted amount", compute='_compute_weighted_amount')

    @api.one
    @api.depends('planned_revenue', 'probability')
    def _compute_weighted_amount(self):
        if not (self.planned_revenue and self.probability):
            self.weighted_amount=0
        else:
            self.weighted_amount=(self.probability/100) * self.planned_revenue