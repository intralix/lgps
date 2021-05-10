# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)


class Device(models.Model):
    _inherit = ['lgps.gpsdevice']

    vehicle_id = fields.Many2one(
        comodel_name="fleet.vehicle",
        string=_("Vehicle"),
        ondelete='set null',
        required=False,
        track_visibility='onchange',
    )
