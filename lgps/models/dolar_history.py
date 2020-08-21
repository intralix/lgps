# -*- coding: utf-8 -*-

from odoo import api, models, fields, _

class Accessory(models.Model):
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = 'lgps.dolar_history'

    name = fields.Char(
        required=True,
        string=_("Internal Id"),
        default="Autogenerated on Save",
    )

    registered_date = fields.Date(
        default=fields.Date.today,
        string=_("Date"),
        track_visibility='onchange'
    )

    conversion_rate = fields.Float(
        digits=(10, 4),
        string=_("Exchange Rate"),
        track_visibility='onchange'
    )

    @api.model
    def create(self, vals):
        seq = self.env['ir.sequence'].next_by_code('lgps.dolar_history') or _('New')
        vals['name'] = seq
        return super(Accessory, self).create(vals)

    @api.multi
    def copy(self, default=None):
        default = dict(default or {})

        copied_count = self.search_count(
            [('name', '=like', u"Copy of {}%".format(self.name))])
        if not copied_count:
            new_name = u"Copy of {}".format(self.name)
        else:
            new_name = u"Copy of {} ({})".format(self.name, copied_count)

        default['name'] = new_name
        return super(Accessory, self).copy(default)

    _sql_constraints = [
        ('name_unique',
         'UNIQUE(name)',
         "The dolar history id must be unique"),
    ]
