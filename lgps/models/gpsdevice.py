# -*- coding: utf-8 -*-
from datetime import timedelta
from odoo import api, models, fields, _
import math
import logging
_logger = logging.getLogger(__name__)


class GpsDevice(models.Model):
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = 'lgps.gpsdevice'

    name = fields.Char(
        required=True,
        string=_("Dispositivo GPS"),
    )

    nick = fields.Char(
        string=_("Nick"),
    )

    imei = fields.Char(
        string=_("IMEI"),
    )

    idf = fields.Char(
        string=_("IDF"),
    )

    installation_date = fields.Date(
        string=_("Installation Date"),
    )

    warranty_start_date = fields.Date(
        string=_("Warranty Start Date"),
    )

    warranty_end_date = fields.Date(
        compute="_compute_end_warranty",
        string=_("Warranty End Date"),
        store=True,
    )

    warranty_term = fields.Selection(
        selection=[
            ("12", _("12 months")),
            ("18", _("18 months")),
            ("24", _("24 months")),
            ("36", _("36 months"))
        ],
        default="12",
        string=_("Warranty Term"),
    )

    tracking = fields.Boolean(
        default=False,
        string=_("Tracking"),
        track_visibility='onchange',
    )

    fuel = fields.Boolean(
        default=False,
        string=_("Fuel"),
        track_visibility='onchange',
    )

    fleetrun = fields.Boolean(
        default=False,
        string=_("Fleetrun"),
        track_visibility='onchange',
    )

    speaker = fields.Boolean(
        default=False,
        string=_("Speaker"),
    )

    anti_jammer_blocker = fields.Boolean(
        default=False,
        string=_("Anti Jammer Blocker"),
    )

    smart_blocker = fields.Boolean(
        default=False,
        string=_("Smart Blocker"),
    )

    blocker = fields.Boolean(
        default=False,
        string=_("Blocker"),
    )

    scanner = fields.Boolean(
        default=False,
        string="Scanner",
        track_visibility='onchange',
    )

    padlock = fields.Boolean(
        default=False,
        string=_("Padlock"),
    )

    solar_panel = fields.Boolean(
        default=False,
        string=_("Solar Panel"),
    )

    temperature = fields.Boolean(
        default=False,
        string=_("Temperature"),
        track_visibility='onchange',
    )

    ibutton = fields.Boolean(
        default=False,
        string=_("iButton"),
    )

    microphone = fields.Boolean(
        default=False,
        string=_("Microphone"),
    )

    sheet = fields.Boolean(
        default=False,
        string=_("Sheet"),
    )

    opening_sensor = fields.Boolean(
        default=False,
        string=_("Opening Sensor"),
    )

    logistic = fields.Boolean(
        default=False,
        string=_("Logistic"),
        track_visibility='onchange',
    )

    disengagement_sensor = fields.Boolean(
        default=False,
        string=_("Disengagement Sensor"),
    )

    datetime_gps = fields.Datetime(
        string=_("DateTime GPS"),
    )

    datetime_server = fields.Datetime(
        string=_("DateTime Server"),
    )

    last_position = fields.Char(
        string=_("Last Position"),
    )

    last_report = fields.Integer(
        string=_("Last Report"),
        compute="_compute_last_report",
        store=True,
        help="Time without reporting in platforms expressed in hours",
    )

    status = fields.Selection(
        selection=[
            ("drop", _("Drop")),
            ("comodato", _("Comodato")),
            ("courtesy", _("Courtesy")),
            ("demo", _("Demo")),
            ("uninstalled", _("Uninstalled")),
            ("external", _("External")),
            ("hibernate", _("Hibernate")),
            ("installed", _("Installed")),
            ("inventory", _("Inventory")),
            ("new", _("New")),
            ("for installing", _("For Installing")),
            ("borrowed", _("Borrowed")),
            ("tests", _("Tests")),
            ("replacement", _("Replacement")),
            ("backup", _("Backup")),
            ("rma", _("RMA")),
            ("sold", _("Sold")),
        ],
        default="inventory",
        string=_("Status"),
        track_visibility='onchange',
    )

    platform = fields.Selection(
        selection=[
            ("Ceiba2", "Ceiba2"),
            ("Cybermapa", "Cybermapa"),
            ("Drop", _("Drop")),
            ("Gurtam", "Gurtam"),
            ("Gurtam_Utrax", "Gurtam/Utrax"),
            ("Mapaloc", "Mapaloc"),
            ("Novit", "Novit"),
            ("Position Logic", "Position Logic"),
            ("Sosgps", "Sosgps"),
            ("Utrax", "Utrax"),
        ],
        string=_("Platform"),
        track_visibility='onchange',
    )

    cellchip_id = fields.Many2one(
        comodel_name="lgps.cellchip",
        string=_("Cellchip Number"),
        ondelete='set null',
        required=False,
        track_visibility='onchange',
    )

    product_id = fields.Many2one(
        comodel_name="product.product",
        required=True,
        string=_("Product Type"),
        index=True,
    )

    invoice_id = fields.Char(
        string=_("Provider Invoice"),
        index=True,
    )

    client_id = fields.Many2one(
        comodel_name="res.partner",
        required=True,
        string=_("Installed On"),
        domain=[
            ('customer', '=', True),
            ('active', '=', True),
            ('is_company', '=', True)
        ],
        index=True,
        track_visibility='onchange',
    )

    suscription_id = fields.One2many(
        comodel_name='sale.subscription',
        inverse_name='gpsdevice_id',
        string=_("Suscription"),
        readonly=True
    )

    serialnumber_id = fields.Many2one(
        comodel_name="stock.production.lot",
        required=True,
        string=_("Serial Number"),
        index=True,
    )

    accessory_ids = fields.One2many(
        comodel_name="lgps.accessory",
        inverse_name="gpsdevice_id",
        string=_("Accessories"),
    )

    tracking_ids = fields.One2many(
        comodel_name="lgps.tracking",
        inverse_name="gpsdevice_id",
        string=_("Trackings"),
    )

    state = fields.Selection(
        [
            ('create', _('Crear')),
            ('assign', _('Asignar')),
            ('program', _('Programar')),
            ('tests', _('Programar')),
            ('installed', _('Instalado')),
        ],
        default='create'
    )

    active = fields.Boolean(
        default=True
    )

    purchase_date = fields.Date(
        default=fields.Date.today,
        string=_("Purchase Date"),
    )

    repairs_ids = fields.One2many(
        comodel_name="repair.order",
        inverse_name="gpsdevice_id",
        string=_("ODT"),
    )

    helpdesk_tickets_ids = fields.One2many(
        comodel_name="helpdesk.ticket",
        inverse_name="gpsdevice_id",
        string=_("Tickets"),
    )

    tasks_ids = fields.One2many(
        comodel_name="project.task",
        inverse_name="gpsdevice_id",
        string=_("Tasks"),
    )

    accesories_count = fields.Integer(
        string=_("Accesories Count"),
        compute='_compute_accesories_count',
    )

    repairs_count = fields.Integer(
        string=_("ODTs"),
        compute='_compute_repairs_count',
    )

    tickets_count = fields.Integer(
        string=_("Tickets Count"),
        compute='_compute_tickets_count',
    )

    trackings_count = fields.Integer(
        string=_("Trackings Count"),
        compute='_compute_trackings_count',
    )

    suscriptions_count = fields.Integer(
        string=_('Subscriptions'),
        compute='_compute_suscriptions_count',
    )

    tasks_count = fields.Integer(
        string=_('Tasks Count'),
        compute='_compute_tasks_count',
    )

    @api.multi
    def _compute_accesories_count(self):
        for rec in self:
            rec.accesories_count = self.env['lgps.accessory'].search_count(
                [('gpsdevice_id', '=', rec.id)])

    @api.multi
    def _compute_repairs_count(self):
        for rec in self:
            rec.repairs_count = self.env['repair.order'].search_count(
                [('gpsdevice_id', '=', rec.id)])

    @api.multi
    def _compute_tickets_count(self):
        for rec in self:
            rec.tickets_count = self.env['helpdesk.ticket'].search_count(
                [('gpsdevice_id', '=', rec.id)])

    @api.multi
    def _compute_trackings_count(self):
        for rec in self:
            rec.trackings_count = self.env['lgps.tracking'].search_count(
                [('gpsdevice_id', '=', rec.id)])

    @api.multi
    def _compute_suscriptions_count(self):
        for rec in self:
            rec.suscriptions_count = self.env['sale.subscription'].search_count(
                [('gpsdevice_id', '=', rec.id)])

    @api.multi
    def _compute_tasks_count(self):
        for rec in self:
            rec.tasks_count = self.env['project.task'].search_count(
                [('gpsdevice_id', '=', rec.id)])

    @api.one
    @api.depends('datetime_gps')
    def _compute_last_report(self):
        if not self.datetime_gps:
            self.last_report = None
        else:
            start_dt = fields.Datetime.from_string(self.datetime_gps)
            today_dt = fields.Datetime.from_string(fields.Datetime.now())
            difference = today_dt - start_dt
            time_difference_in_hours = difference.total_seconds() / 3600
            self.last_report = math.ceil(time_difference_in_hours)

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

        return super(GpsDevice, self).copy(default)

    _sql_constraints = [
        ('name_unique',
         'UNIQUE(name)',
         "The gps device id must be unique"),
    ]
