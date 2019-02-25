# -*- coding: utf-8 -*-
from odoo import api, models, fields, _


class Tracking(models.Model):
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = 'lgps.tracking'

    name = fields.Char(
        required=True,
        string="Tracking Id",
        default="Autogenerated on Save"
    )

    client_id = fields.Many2one(
        comodel_name="res.partner",
        string="Client Account",
        index=True,
    )

    gpsdevice_id = fields.Many2one(
        comodel_name="lgps.gpsdevice",
        string="Gps Device",
        index=True,
    )

    applicant = fields.Char(
        string="Requested By",
    )

    state = fields.Selection(
        [
            ('registered', _('Registrado')),
            ('active', _('Activo')),
            ('paused', _('Detenido')),
            ('finished', _('Finalizado')),
            ('billed', _('Facturado')),
        ],
        string="State",
        default="registered",
    )

    category = fields.Selection(
        [
            ('event', _('Per Event')),
            ('permanent', _('Permanente')),
            ('uninterrupted ', _('Uninterrupted')),
        ],
        string="Category",
        default="event",
        index=True,
    )

    driver = fields.Char(
        string="Driver",
    )

    phone = fields.Text(
        string="Phones",
    )

    notifications = fields.Text(
        string="Notifications",
    )

    notify = fields.Boolean(
        string="Notify Client",
        default=False
    )

    initial_date = fields.Date(
        default=fields.Date.today,
        string="Initial Date",
    )

    final_date = fields.Date(
        default=fields.Date.today,
        string="Final Date",
    )

    origin = fields.Text(
        string="Origin",
    )

    destination = fields.Text(
        string="Destination",
    )

    route = fields.Text(
        string="Route",
    )

    observations = fields.Text(
        string="Observations",
    )

    start_date = fields.Datetime(
        string="Activity Started at"
    )

    end_date = fields.Datetime(
        string="Activity finished at"
    )

    @api.model
    def create(self, vals):
        seq = self.env['ir.sequence'].next_by_code('lgps.tracking') or '/'
        vals['name'] = seq
        return super(Tracking, self).create(vals)
