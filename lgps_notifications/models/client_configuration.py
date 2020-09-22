# -*- coding: utf-8 -*-

from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import api, models, fields, _
import logging

_logger = logging.getLogger(__name__)


class ClientConfigurations(models.Model):
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = 'lgps.client_configuration'

    def _default_clients(self):
        client_id_list = []
        configured = self.env['lgps.client_configuration'].search([])
        if configured:
            for client in configured:
                client_id_list.append(client.client_id.id)

        return [('customer', '=', True), ('active', '=', True),
                ('is_company', '=', True), ('id', 'not in', client_id_list)]

    name = fields.Char(
        required=True,
        string=_("Internal Id"),
        default="Autogenerated on Save",
    )

    operative = fields.Boolean(
        string=_("Active"),
        default=True,
    )

    priority = fields.Selection(
        selection=[
            ("asc", _("From lower to higher")),
            ("desc", _("From higher to lower")),
        ],
        default="desc",
        string=_("Priority"),
        help=_("This option set the evaluation method when multiple rules are attached to the record based on the "
               "hours of each rule.\n The priority its switched as described in the option")
    )

    staggered = fields.Boolean(
        string=_("staggered"),
        default=False,
        # readonly=True,
        help=_("This option will trigger notifications in steps from lower to higher "
               "rules when multiple rules are defined.")
    )

    client_id = fields.Many2one(
        comodel_name="res.partner",
        domain=_default_clients,
        ondelete="set null",
        required=True,
    )

    rule_ids = fields.Many2many(
        comodel_name='lgps.notification_rules',
        relation="offline_rules_conf",
        string=_("Offline Notification Rules"),
    )

    contact_ids = fields.Many2many(
        comodel_name="res.partner",
    )

    repeat_alerts = fields.Selection(
        selection=[
            ("repeat", _("Repeat")),
            ("no_repeat", _("No repeat")),
        ],
        defaul="repeat",
        string=_("Reset Alerts"),
        help=_("Reset the staggered notifications on devices that has already passed all configured alerts.")
    )

    reset_options = fields.Selection(
        selection=[
            ("1", _("1 Month")),
            ("3", _("3 Months")),
            ("6", _("6 months")),
            ("12", _("12 months")),
        ],
        default="1",
        string=_("Repeat on"),
        help=_("Configured hold time to reset staggered notifications when devices has already "
               "passed all configured alerts.")
    )

    @api.model
    def create(self, vals):
        seq = self.env['ir.sequence'].next_by_code('lgps.client_configuration') or _('New')
        vals['name'] = seq
        return super(ClientConfigurations, self).create(vals)

    @api.onchange('client_id')
    def _onchange_client_id(self):
        domain = {}
        client_id_list = []
        configured = self.sudo().env['lgps.client_configuration'].search([])
        if configured:
            for client in configured:
                client_id_list.append(client.client_id.id)

        domain = {'client_id': [
            ('customer', '=', True), ('active', '=', True),
            ('is_company', '=', True), ('id', 'not in', client_id_list)
        ]}

        return {'domain': domain}

    @api.onchange('priority')
    def _onchange_priority_id(self):
        if self.priority == 'asc':
            self.staggered = True
            self.repeat_alerts = 'repeat'
        else:
            self.staggered = False
            self.reset_alerts = 'no_repeat'

    @api.onchange('staggered')
    def _onchange_staggered(self):
        if self.staggered:
            self.staggered = True
            self.reset_alerts = 'repeat'
        else:
            self.priority = 'desc'
            self.staggered = False
            self.reset_alerts = 'no_repeat'

    @api.model
    def _cron_generate_notifications(self):
        """
            Generates notifications for configurations defined
        """
        #_logger.warning('Order by: %s', self.priority)
        order = True if self.priority == 'desc' else False
        rule_lists = {}

        configurations = self.sudo().env['lgps.client_configuration'].search([('operative', '=', True)])
        #_logger.warning('Configurations found: %s', configurations)

        # Iterate records in this configuration
        for cnf in configurations:
            #_logger.warning('Current Configuration: %s', cnf.name)
            if cnf.rule_ids:
                rules = cnf.rule_ids
                #_logger.warning('Rules found: %s', rules)

                sorted_rules = rules.sorted(key=lambda r: r.hours_rule, reverse=order)
                for rule in sorted_rules:
                    rule_lists[str(rule.id)] = []

                gps_devices = self.sudo().env['lgps.gpsdevice'].search([
                    ('client_id', "=", cnf.client_id.id),
                    ('notify_offline', "=", True)
                ])
                _logger.error('Devices Configured: %s', gps_devices)

                if cnf.priority == 'asc':
                    if gps_devices:
                        for device in gps_devices:
                            # _logger.warning('Device: %s with hours %s offline', device.name, device.last_report)
                            # if device.last_rule_applied:
                            #     _logger.warning('Last Rule Applied: %s', device.last_rule_applied)
                            if not device.last_rule_applied:
                                last_rule_hours = device.last_report
                                _logger.warning('Not Rule Applied Yet, using last_report %s', last_rule_hours)
                            else:
                                last_rule_hours = device.last_rule_applied.hours_rule
                                _logger.warning('Last Rule Applied: %s', device.last_rule_applied)

                            for rule in sorted_rules:
                                _logger.warning('Last Rule: %s vs Current Rule %s', last_rule_hours, rule.hours_rule)
                                if last_rule_hours > rule.hours_rule:
                                    #_logger.warning('device.last_report: %s vs rule.hours_rule %s', device.last_report, rule.hours_rule)
                                    if last_rule_hours > rule.hours_rule:
                                        _logger.warning('Apply Rule: %s', rule.name)
                                        rule_lists[str(rule.id)].append(device.id)
                                        device.write({
                                            'last_rule_applied': rule.id,
                                            'last_rule_applied_on': datetime.today()
                                        })
                                        break
                                    else:
                                        _logger.warning('No rules apply: %s - %s ', device.name, rule.name)
                                # else:
                                #     _logger.warning('NNo se han sobrepasado las reglas de tiempo %s vs %s',  rule.hours_rule, last_rule_hours)
                else:
                    if gps_devices:
                        for device in gps_devices:
                            for rule in sorted_rules:
                                if device.last_report > rule.hours_rule:
                                    #_logger.warning('Apply Rule: %s', rule.name)
                                    rule_lists[str(rule.id)].append(device.id)
                                #else:
                                    #_logger.warning('No rules apply: %s - %s ', device.name, rule.name)

            #_logger.warning('Lists: %s', rule_lists)
            for infraction in rule_lists:
                if len(rule_lists[infraction]) > 0:
                    #_logger.warning('Infraction: %s', rule_lists[infraction])
                    record = self.create_notification(cnf, infraction, rule_lists[infraction])
                    #_logger.warning('Notification created: %s', record.name)
        return

    @api.multi
    def test_generate_notifications(self):
        self._cron_generate_notifications()
        return

    def create_notification(self, record, rule, devices):

        notification_object = self.env['lgps.notification']

        dictionary = {
            'description': 'Notificación generada por sistema',
            'rule_id': rule,
            'client_id': record.client_id.id,
            'gpsdevice_ids': [(6, _, devices)],
            'contact_ids': [(6, _, record.contact_ids.ids)]
        }
        return notification_object.create(dictionary)

    @api.model
    def _cron_reset_device_notifications(self):
        """
            Generates maintenance request on the next_action_date or today if none exists
        """
        # Iterate records in this configuration
        clients_configuration = self.sudo().env['lgps.client_configuration'].search([
            ('operative', '=', True),
            ('repeat_alerts', '=', 'repeat'),
            ('reset_options', '!=', None)
        ])

        #_logger.warning('Configurations found: %s', clients_configuration)

        for cnf in clients_configuration:
            #_logger.warning('Cliente: %s', cnf.client_id.name)
            #_logger.warning('Current Configuration Options: %s', cnf.reset_options)

            devices = self.sudo().env['lgps.gpsdevice'].search([
                ('notify_offline', '=', True),
                ('client_id', '=', cnf.client_id.id)
            ])
            #_logger.warning('Dispositivos Found: %s', devices)
            for device in devices:
                #_logger.warning('Device: %s', device.name)
                last_rule = fields.Date.from_string(device.last_rule_applied_on)
                #_logger.warning('Last Rule on: %s', last_rule)
                if last_rule is not None:
                    months = int(cnf.reset_options)
                    #_logger.warning('Months: %s', months)
                    if months > 0:
                        expiration_date = device.last_rule_applied_on + relativedelta(months=months)
                        #_logger.error('Expiration Date: %s', expiration_date)
                        #_logger.error('Today: %s', datetime.today().date())
                        if datetime.today().date() > expiration_date:
                            #_logger.error('Reseting device')
                            device.write({
                                'last_rule_applied': None,
                                'last_rule_applied_on': None
                            })
        return

    @api.multi
    def test_cron_reset_device_notifications(self):
        self._cron_reset_device_notifications()
        return
