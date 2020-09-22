# -*- coding: utf-8 -*-

from odoo import api, models, fields, _


class OfflineGpsDevice(models.Model):
    _inherit = 'lgps.gpsdevice'

    notify_offline = fields.Boolean(
        default=False,
        string=_("Notify offline"),
        track_visibility='onchange',
        help=_("When checked it will be evaluated to send notifications")
    )

    notifications_count = fields.Integer(
        string=_('Notifications Count'),
        compute='_compute_notifications_count',
    )

    last_rule_applied = fields.Many2one(
        comodel_name="lgps.notification_rules",
        string=_("Last Notification"),
        ondelete="set null"
    )

    last_rule_applied_on = fields.Date(
        string=_("Last Notification On"),
        ondelete="set null",
        help=_("Date when last notification was sent. If client configuration it set to reset notifications, the reset "
               "option configuration will be sum to this date for evaluate if is necessary to restart notifications "
               "on this device.")
    )

    @api.multi
    def _compute_notifications_count(self):
        for rec in self:
            rec.notifications_count = self.env['lgps.notification'].search_count([
                ('gpsdevice_ids', 'in', [rec.id])
            ])
