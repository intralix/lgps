# -*- coding: utf-8 -*-

from odoo import api, models, fields, _


class NotificationRule(models.Model):
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = 'lgps.notification_rules'

    name = fields.Char(
        required=True,
        string=_("Reference"),
    )

    description = fields.Text(
        required=True,
        string=_("Description"),
    )

    hours_rule = fields.Integer(
        required=True,
        string=_("Time Rule based on hours"),
    )

    is_active = fields.Boolean(
        string=_("Is active"),
        default=False
    )

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
        return super(NotificationRule, self).copy(default)
