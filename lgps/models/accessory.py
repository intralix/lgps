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

    provider_invoice = fields.Char(
        string="Provider Invoice",
        index=True,
    )

    purchase_date = fields.Date(
        default=fields.Date.today,
        string="Purchase Date",
    )

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
