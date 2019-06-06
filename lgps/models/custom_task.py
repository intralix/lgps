# -*- coding: utf-8 -*-

from datetime import timedelta
from odoo import api, models, fields, _
from odoo.exceptions import Warning


class Task(models.Model):
    _inherit = ['project.task']

    gpsdevice_id = fields.Many2one(
        comodel_name="lgps.gpsdevice",
        string=_("Gps Device"),
        ondelete="set null",
        index=True,
    )



