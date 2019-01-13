# -*- coding: utf-8 -*-

from datetime import timedelta
from odoo import api, models, fields, _

class Accessory(models.Model):
    _inherit = ['mail.thread']
    _name = 'lgps.accessory'

    name = fields.Char(
        required=True,
        string="Internal Id",
    )

    serialnumber_id = fields.Many2one(
        comodel_name="stock.production.lot",
        required=True,
        string="Serial Number",
        index=True,
    )

    client_id = fields.Many2one(
        comodel_name="res.partner",
        required=True,
        string="Client",
        domain=[
            ('customer', '=', True),
            ('active', '=', True),
            ('is_company', '=', True)
        ],
        index=True,
    )

    gpsdevice_id = fields.Many2one(
        comodel_name="lgps.gpsdevice",
        ondelete="cascade",
        string="Installed On",
        index=True,
    )

    installation_date = fields.Date(
        default=fields.Date.today,
        string="Installation Date",
    )

    status = fields.Selection(
        selection=[
            ("Baja", "Baja"),
            ("Comodato", "Comodato"),
            ("Cortesía", "Cortesía"),
            ("Demo", "Demo"),
            ("Desinstalado", "Desinstalado"),
            ("Externo", "Externo"),
            ("Hibernado", "Hibernado"),
            ("Instalado", "Instalado"),
            ("Inventario", "Inventario"),
            ("Nuevo", "Nuevo"),
            ("Por Instalar", "Por Instalar"),
            ("Prestado", "Prestado"),
            ("Pruebas", "Pruebas"),
            ("Reemplazo", "Reemplazo"),
            ("Respaldo", "Respaldo"),
            ("Vendido", "Vendido")
        ],
        default="Inventario",
        string="Status",
    )

    product_id = fields.Many2one(
        comodel_name="product.product",
        required=True,
        string="Product Type",
        index=True
    )

    invoice_id = fields.Many2one(
        comodel_name="account.invoice",
        required=True,
        string="Invoice",
        index=True,
    )

    warranty_start_date = fields.Date(
        default=fields.Date.today,
        string="Warranty Start Date",
    )

    warranty_end_date = fields.Date(
        compute="_compute_end_warranty",
        string="Warranty End Date",
    )

    warranty_term = fields.Selection(
        selection=[
            ("12", _("12 months")),
            ("18", _("18 months")),
            ("24", _("24 months")),
            ("36", _("36 months"))
        ],
        default="12",
        string="Warranty Term",
    )

    @api.one
    @api.depends('warranty_term', 'warranty_start_date')
    def _compute_end_warranty(self):
        if not (self.warranty_term and self.warranty_start_date):
            self.warranty_end_date = None
        else:
            months = int(self.warranty_term[:2])
            start = fields.Date.from_string(self.warranty_start_date)
            self.warranty_end_date = start + timedelta(months * 365 / 12)

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
        return super(Accessory, self).copy(default)

    _sql_constraints = [
        ('name_unique',
         'UNIQUE(name)',
         "The accessory id must be unique"),
    ]
