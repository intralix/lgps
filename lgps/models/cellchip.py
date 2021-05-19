# -*- coding: utf-8 -*-
from odoo import api, models, fields, _


class Cellchip(models.Model):
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = 'lgps.cellchip'

    # Línea Celular
    name = fields.Char(
        required=True,
        string=_("Line Number"),
    )

    gpsdevice_id = fields.One2many(
        comodel_name='lgps.gpsdevice',
        inverse_name='cellchip_id',
        string=_("Installed On"),
        help="GPS Device where the cellchip is on.",
        readonly=True,
        track_visibility='onchange'
    )

    # Estatus de la Línea
    status = fields.Selection(
        selection=[
            ("active", _("Active")),
            ("cancelled", _("Cancelled")),
            ("replaced", _("Replaced")),
            ("suspended", _("Suspended")),
        ],
        default="active",
        string=_("Status"),
        track_visibility='onchange'
    )
    # Plan de la línea
    plan = fields.Selection(
        selection=[
            ("20KB", "20KB"),
            ("100KB", "100KB"),
            ("1MB", "1MB"),
            ("2MB", "2MB"),
            ("3MB", "3MB"),
            ("5MB", "5MB"),
            ("10MB", "10MB"),
            ("15MB", "15MB"),
            ("100MB", "100MB"),
            ("500MB", "500MB"),
            ("1GB", "1GB"),
            ("3GB", "3GB"),
            ("5GB", "5GB"),
            ("10GB", "10GB")
        ],
        string="Plan",
        track_visibility='onchange'
    )
    # Número de Serie
    linenumber_id = fields.Many2one(
        comodel_name="stock.production.lot",
        required=True,
        string=_("SIMCARD"),
        index=True,
    )
    # Si la línea Voz
    voice = fields.Boolean(
        default=False,
        string="Voice",
    )
    # A quién esta asignado
    cellchip_owner_id = fields.Many2one(
        comodel_name="res.partner",
        domain=[
            ('customer', '=', True),
            ('active', '=', True),
            ('is_company', '=', True)
        ],
        string=_("Cellchip Owner"),
        index=True,
        track_visibility='onchange'
    )
    # Proveedor de la línea
    provider = fields.Selection(
        selection=[
            ("ATT", "ATT"),
            ("Cierto", "Cierto"),
            ("CiertoT", "CiertoT"),
            ("Iusacell", "Iusacell"),
            ("MazTiempo", "MazTiempo"),
            ("Movistar", "Movistar"),
            ("Prossea", "Prossea"),
            ("Simpacsys", "Simpacsys"),
            ("Skywave", "Skywave"),
            ("Telcel", "Telcel"),
        ],
        string="Provider",
        track_visibility='onchange'
    )
    # Plazo de la línea
    term = fields.Selection(
        selection=[
            ("12", "12"),
            ("18", "18"),
            ("24", "24")
        ],
        string=_("Line Terms"),
        track_visibility='onchange'
    )

    # Fecha de Compra
    purchase_date = fields.Date(
        default=fields.Date.today,
        string=_("Purchase Date"),
    )

    # Cuenta de Lineas
    major_account = fields.Char(
        string=_("Mayor Accounte"),
    )

    # Cuenta de Lineas
    line_account = fields.Char(
        string=_("Line Account"),
    )

    #
    status_date = fields.Date(
        string=_("Status Date"),
    )

    # Fecha de finalización del Plan Forzoso
    end_forced_plan_date = fields.Date(
        string=_("End Forced Plan Date"),
    )

    # Si la linea esta ocupada o no
    taken = fields.Boolean(
        default=False,
        string=_("Taken"),
    )

    # Días desde que la línea se marco como suspendida
    days_suspended = fields.Integer(
        string=_("Status Elpased Days"),
        compute="_compute_days_suspended",
        store=True,
        help="Time elapsed since the line was set to suspended expressed in days",
    )

    @api.onchange('status')
    def onchange_status_date(self):
        if self.status == 'suspended':
            self.status_date = fields.Date.today()

    @api.one
    @api.depends('status_date')
    def _compute_days_suspended(self):
        if not self.status_date:
            self.days_suspended = None
        elif self.status == 'suspended':
            start_dt = fields.Datetime.from_string(self.status_date)
            today_dt = fields.Datetime.from_string(fields.Datetime.now())
            difference = today_dt - start_dt
            self.days_suspended = difference.total_seconds() / 3600 / 24
        else:
            self.days_suspended = None

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
        return super(Cellchip, self).copy(default)

    _sql_constraints = [
        ('name_unique',
         'UNIQUE(name)',
         "The cellchip id must be unique"),
    ]
