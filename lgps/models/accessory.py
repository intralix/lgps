# -*- coding: utf-8 -*-

from datetime import timedelta
from odoo import api, models, fields, _
from odoo.exceptions import Warning


class Accessory(models.Model):
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = 'lgps.accessory'

    name = fields.Char(
        required=True,
        string="Internal Id",
        default="Autogenerated on Save",
    )

    serialnumber_id = fields.Many2one(
        comodel_name="stock.production.lot",
        string="Serial Number",
        index=True,
    )

    client_id = fields.Many2one(
        comodel_name="res.partner",
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
        ondelete="set null",
        string="Installed On",
        index=True,
    )

    installation_date = fields.Date(
        default=fields.Date.today,
        string="Installation Date",
    )

    status = fields.Selection(
        selection=[
            ("drop", "Drop"),
            ("comodato", _("Comodato")),
            ("courtesy", _("Courtesy")),
            ("demo", _("Demo")),
            ("uninstalled", _("Uninstalled")),
            ("external", _("External")),
            ("hibernate", _("Hibernate")),
            ("installed", _("Installed")),
            ("inventory", _("Inventory")),
            ("new", _("New")),
            ("ready", _("Ready to Install")),
            ("borrowed", _("Borrowed")),
            ("tests", _("Tests")),
            ("replacement", _("Replacement")),
            ("backup", _("Backup")),
            ("rma", _("RMA")),
            ("sold", _("Sold")),
        ],
        default="inventory",
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

    @api.model
    def create(self, vals):
        seq = self.env['ir.sequence'].next_by_code('lgps.accessory') or _('New')
        vals['name'] = seq
        return super(Accessory, self).create(vals)

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

    @api.multi
    def btn_remove_from_gpsdevice(self):
        for accesory in self:
            if not accesory.gpsdevice_id:
                raise Warning('El accesorio %s no esta asignado a un dispositivo gps' % accesory.name)
            else:
                today = fields.Date.today()
                gpsdevice = accesory.gpsdevice_id

                gpsdevice.message_post(
                    body="Accesorio <b>" + accesory.name + "</b> desinstalado el día <b>" + today.strftime(
                        '%d-%m-%Y') + "</b> <br>No Serie: <b>" + accesory.serialnumber_id.name + "</b>")

                accesory.message_post(
                    body="Accesorio desinstalado del equipo <b>" + gpsdevice.name + "</b> el día <b>" + today.strftime(
                        '%d-%m-%Y') +'</b>')

                accesory.write({'gpsdevice_id': None, 'status': 'uninstalled'})
        return True
