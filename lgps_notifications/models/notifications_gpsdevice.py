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

    last_rule_applied_on = fields.Date(
        string=_("Last Notification On"),
        ondelete="set null"
    )

    # reset_on = fields.Date(
    #      string=_("Should Reset on"),
    #      compute='_compute_reset_on',
    #      store=True
    # )

    needs_reset = fields.Boolean(
        string=_("Needs Reset"),
        help=_("Configured time to reset  staggered notifications accomplished.")
    )

    @api.multi
    def _compute_notifications_count(self):
        for rec in self:
            rec.notifications_count = self.env['lgps.notification'].search_count([
                ('gpsdevice_ids', 'in', [rec.id])
            ])

    # @api.depends('last_rule_applied_on')
    # def _compute_reset_on(self):
    #     if self.reset_options < 0:
    #         self.reset_on = None
    #     else:
    #         months = int(self.reset_options)
    #         start = fields.Date.from_string(self.last_rule_applied_on)
    #         self.reset_on = start + timedelta(months * 365 / 12)