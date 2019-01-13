# -*- coding: utf-8 -*-
from odoo import api, models, fields, _

class Cellchip(models.Model):
    _inherit = ['mail.thread']
    _name = 'lgps.cellchip'

    name = fields.Char(
        required=True,
        string="Line Number",
    )

    status = fields.Selection(
        selection=[
            ("active", _("Active")),
            ("drop", _("Drop")),
            ("suspended", _("Suspended")),
            ("reactivated", _("Reactivated")),
            ("replaced", _("Replaced"))
        ],
        default="Activa",
        string="Status",
    )

    plan = fields.Selection(
        selection=[
            ("20KB", "20KB"),
            ("100KB", "100KB"),
            ("1MB", "1MB"),
            ("2MB", "2MB"),
            ("3MB", "3MB"),
            ("5MB", "5MB"),
            ("10MB", "10MB"),
            ("100MB", "100MB"),
            ("500MB", "500MB"),
            ("1GB", "1GB"),
            ("3GB", "3GB"),
            ("5GB", "5GB"),
            ("10GB", "10GB")
        ],
        string="Plan",
    )

    linenumber_id = fields.Many2one(
        comodel_name="stock.production.lot",
        required=True,
        string="SIMCARD",
        index=True,
    )

    voice = fields.Boolean(
        default=False,
        string="Voice",
    )

    cellchip_owner_id = fields.Many2one(
        comodel_name="res.partner",
        domain=[
            ('customer', '=', True),
            ('active', '=', True),
            ('is_company', '=', True)
        ],
        string="Cellchip Owner",
        index=True,
    )

    provider = fields.Selection(
        selection=[
            ("ATT", "ATT"),
            ("Cierto", "Cierto"),
            ("Iusacell", "Iusacell"),
            ("Movistar", "Movistar"),
            ("Prossea", "Prossea"),
            ("Sinpacsys", "Sinpacsys"),
            ("Telcel", "Telcel")
        ],
        string="Provider",
    )

    warranty_payment_date = fields.Date(
        default=fields.Date.today,
        string="Warranty Payment Date",
    )

    taken = fields.Boolean(
        default=False,
        string="Taken",
    )
