# -*- coding: utf-8 -*-
from odoo import api, models, fields, _

class Cellchip(models.Model):
    _inherit = ['mail.thread']
    _name = 'lgps.cellchip'
    # Línea Celular
    name = fields.Char(
        required=True,
        string="Line Number",
    )
    # Estatus de la Línea
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
    #Plan de la línea
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
    # Número de Serie
    linenumber_id = fields.Many2one(
        comodel_name="stock.production.lot",
        required=True,
        string="SIMCARD",
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
        string="Cellchip Owner",
        index=True,
    )
    # Proveedor de la línea
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
    # Plazo de la línea
    term = fields.Selection(
        selection=[
            ("12", "12"),
            ("18", "18"),
            ("24", "24")
        ],
        string="Line Terms",
    )

    # Fecha de Compra
    purchase_date = fields.Date(
        default=fields.Date.today,
        string="Purchase Date",
    )

    # Cuenta de Lineas
    major_account = fields.Char(
        string="Mayor Accounte",
    )

    # Cuenta de Lineas
    line_account = fields.Char(
        string="Line Account",
    )

    #
    status_date = fields.Date(
        default=fields.Date.today,
        string="Warranty Payment Date",
    )

    # Fecha de finalización del Plan Forzoso
    end_forced_plan_date = fields.Date(
        default=fields.Date.today,
        string="End Forced Plan Date",
    )

    #Si la linea esta ocupada o no
    taken = fields.Boolean(
        default=False,
        string="Taken",
    )

    # Días desde que la línea se marco como suspendida
    days_suspended = fields.Integer(
        string="Estatus Elpased Days",
        compute="_compute_days_suspended",
        store=True,
        help="Time elapsed since the line was set to suspended expressed in days",
    )

    @api.one
    @api.depends('status_date', 'days_suspended')
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