# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)


class Vehicle(models.Model):
    _inherit = ['fleet.vehicle']

    nick = fields.Char(
        string=_("Nick"),
    )

    gpsdevice_id = fields.One2many(
        comodel_name='lgps.gpsdevice',
        inverse_name='vehicle_id',
        string=_("Installed On"),
        help="GPS Device associated to this vehicle.",
        track_visibility='onchange'
    )

    client_id = fields.Many2one(
        comodel_name="res.partner",
        required=False,
        string=_("Account"),
        domain=[
            ('customer', '=', True),
            ('is_company', '=', True)
        ],
        index=True,
        track_visibility='onchange',
    )

    vehicle_type_id = fields.Many2one(
        comodel_name="lgps.vehicle.type",
        required=False,
        string=_("Vehicle Type"),
        index=True,
    )


class VehicleType(models.Model):

    _name = "lgps.vehicle.type"
    _description = "Vehicle Type"

    name = fields.Char('Name', required=True, translate=True)

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Vehicle type already exist !"),
    ]
