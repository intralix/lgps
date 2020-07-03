# -*- coding: utf-8 -*-

from datetime import timedelta
from odoo import api, models, fields, _
from odoo.exceptions import Warning


class DeviceHistory(models.Model):
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = 'lgps.device_history'

    name = fields.Char(
        required=True,
        string=_("Internal Id"),
        default="Autogenerated on Save",
    )

    serialnumber_id = fields.Many2one(
        comodel_name="stock.production.lot",
        string=_("Serial Number"),
    )

    client_id = fields.Many2one(
        comodel_name="res.partner",
        string=_("Client"),
        domain=[
            ('customer', '=', True),
            ('active', '=', True),
            ('is_company', '=', True)
        ],
    )

    gpsdevice_ids = fields.Many2one(
        comodel_name='lgps.gpsdevice',
        string="Gps Device",
        required=True,
    )

    destination_gpsdevice_ids = fields.Many2one(
        comodel_name='lgps.gpsdevice',
        string=_("Substitute equipment"),
    )

    product_id = fields.Many2one(
        comodel_name="product.product",
        string=_("Product Type"),
    )
    operation_mode = fields.Selection(
        [
            ('drop', _('Baja de Equipos')),
            ('hibernation', _('Hibernación de Equipos')),
            ('wakeup', _('Deshibernación de Equipos')),
            ('replacement', _('Reemplazo de Equipo')),
            ('substitution', _('Sustitución de equipo por revisión')),
            ('accsubstitution', _('Sustitución de accesorio por revisión')),
            ('accreplacement', _('Reemplazo de accesorio')),
            ('add_reactivate', _('Alta / Reactivación Equipo')),
        ],
        default='drop',
    )

    reason = fields.Selection(
        [
            ('bad_service', _('Mal Servicio')),
            ('vehicle_sold', _('Venta de Unidad')),
            ('wrecked_vehicle', _('Unidad siniestrada')),
            ('client_warehouse', _('Sin uso, en resguardo con el cliente')),
            ('own_warehouse', _('Error administrativo')),
            ('non_repairable', _('Equipo gps no reparable')),
            ('financial_situation', _('Cancelación de cuenta por falta de pago')),
            ('change_of_supplier', _('Cambio de proveedor por precio')),
            ('return_to_stock', _('Regresa a Almacén Respaldo/Provisional/Prestado')),
            ('return_from_loan', _('Regresa a Almacén Estuvo en Comodato')),
            ('on_stock_not_assigned', _('En almacén Intralix sin asignación')),
        ],
    )

    related_odt = fields.Many2one(
        comodel_name='repair.order',
        string=_("Work order related"),
    )

    requested_by = fields.Char(
        string=_("Requested by"),
    )

    comment = fields.Text(
        string=_("Operation Reason"),
    )

    log_msn = fields.Html(
        string=_("More Info"),
    )

    @api.model
    def create(self, vals):
        seq = self.env['ir.sequence'].next_by_code('lgps.device_history') or _('New')
        vals['name'] = seq
        return super(DeviceHistory, self).create(vals)

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
        return super(DeviceHistory, self).copy(default)

    _sql_constraints = [
        ('name_unique',
         'UNIQUE(name)',
         "The accessory id must be unique"),
    ]
