# -*- coding: utf-8 -*-
from datetime import timedelta
from odoo import api, models, fields, _
import math
import logging
_logger = logging.getLogger(__name__)


class OfflineGpsDevice(models.Model):
    _inherit = 'lgps.gpsdevice'

    notify_offline = fields.Boolean(
        default=False,
        string=_("Notify offline"),
        track_visibility='onchange',
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

    @api.multi
    def _compute_notifications_count(self):
        for rec in self:
            rec.notifications_count = self.env['lgps.notification'].search_count([
                ('gpsdevice_ids', 'in', [rec.id])
            ])

