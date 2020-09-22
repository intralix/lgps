# -*- coding: utf-8 -*-

from odoo import api, models, fields, _
import re
import logging
_logger = logging.getLogger(__name__)


class Failures(models.Model):
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = 'lgps.failures'
    _description = "Fallas"

    name = fields.Char(
        required=True,
        string=_("Internal Id"),
        default="Autogenerated on Save",
    )

    product_id = fields.Many2one(
        comodel_name="product.product",
        required=True,
        string=_("Product Type"),
        ondelete="set null",
        index=True,
    )

    client_id = fields.Many2one(
        comodel_name="res.partner",
        string=_("Installed On"),
        domain=[
            ('customer', '=', True),
            ('active', '=', True),
            ('is_company', '=', True)
        ],
        index=True,
        track_visibility='onchange',
    )

    failure_symptoms_list_id = fields.Many2one(
        comodel_name="lgps.failure_symptoms_list",
        string=_("Failure Symptoms List"),
        ondelete="set null",
        index=True,
    )

    failure_functionalities_list_id = fields.Many2one(
        comodel_name="lgps.failure_functionalities_list",
        string=_("Failure Funtionalities List"),
        ondelete="set null",
        index=True,
    )

    failure_components_list_id = fields.Many2one(
        comodel_name="lgps.failure_components_list",
        string=_("Failure Components List"),
        ondelete="set null",
        index=True,
    )

    failure_root_problem_list_id = fields.Many2one(
        comodel_name="lgps.failure_root_problem_list",
        string=_("Failure Root Problem List"),
        ondelete="set null",
        index=True,
    )

    report_date = fields.Date(
        default=fields.Date.today,
        string=_("Report Date"),
        track_visibility='onchange',
    )

    serialnumber_id = fields.Many2one(
        comodel_name="stock.production.lot",
        string=_("Serial Number"),
        ondelete="set null",
        index=True,
    )

    repairs_id = fields.Many2one(
        comodel_name="repair.order",
        ondelete="set null",
        string=_("ODT"),
        index=True,
        track_visibility='onchange',
        required="True"
    )

    internal_notes = fields.Text(
        string=_('Internal Notes')
    )

    manipulation_detected = fields.Boolean(
        string=_("Detected Manipulation"),
        default=False
    )

    # root_problem_invalidate = fields.Many2one(
    #     'lgps.failure_root_problem_list',
    #     string='lgps.failure_root_problem_list',
    #     related='id.invalidate',
    # )

    time_spent = fields.Float(
        string=_("Time Spent"),
        help='Time spent in solution to this record',
        track_visibility='onchange'
    )

    @api.model
    def create(self, vals):
        seq = self.env['ir.sequence'].next_by_code('lgps.failures') or _('New')
        vals['name'] = seq
        return super(Failures, self).create(vals)

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
        return super(Failures, self).copy(default)

    _sql_constraints = [
        ('name_unique',
         'UNIQUE(name)',
         "The failure id must be unique"),
    ]

    @api.onchange('failure_symptoms_list_id')
    def _onchange_failure_failure_symptoms_list_id(self):
        domain = {}
        if self.failure_symptoms_list_id.name:
            if re.search('manipulaci',self.failure_symptoms_list_id.name, re.IGNORECASE):
                self.manipulation_detected = True
            else:
                self.manipulation_detected = False
                self.failure_functionalities_list_id = None
                self.failure_components_list_id = None
                self.failure_root_problem_list_id = None

        return domain

    @api.onchange('failure_functionalities_list_id')
    def _onchange_failure_functionalities_list_id(self):
        domain = {}
        if self.failure_functionalities_list_id:
            list_ids = []
            values = self.env['lgps.failure_components_list'].search(
                [('failure_functionalities_list_id', '=', self.failure_functionalities_list_id.id)])

            for value in values:
                list_ids.append(value.id)

            self._check_no_warranty_rules(self.failure_functionalities_list_id.name)
            self.failure_components_list_id = []
            self.failure_root_problem_list_id = []

            domain = {
                'failure_components_list_id': [('id', 'in', list_ids)],
            }

        return {'domain': domain}

    @api.onchange('failure_components_list_id')
    def _onchange_failure_components_list_id(self):
        domain = {}
        if self.failure_components_list_id:
            list_ids = []
            values = self.env['lgps.failure_root_problem_list'].search(
                [('failure_components_list_id', '=', self.failure_components_list_id.id)])

            for value in values:
                list_ids.append(value.id)

            self._check_no_warranty_rules(self.failure_components_list_id.name)
            self.failure_root_problem_list_id = []
            domain = {'failure_root_problem_list_id': [('id', 'in', list_ids)]}

        return {'domain': domain}

    @api.onchange('failure_root_problem_list_id')
    def _onchange_failure_root_problem_list_id(self):
        if self.failure_root_problem_list_id:
            self._check_no_warranty_rules(self.failure_root_problem_list_id.name)
            self._check_if_invalidate(self.failure_root_problem_list_id.invalidate)
        return

    def _check_no_warranty_rules(self, field):
        if not self.manipulation_detected:
            if field:
                if re.search('manipulaci', field, re.IGNORECASE):
                    self.manipulation_detected = True
                else:
                    self.manipulation_detected = False

        return

    def _check_if_invalidate(self, invalidate):
        if not self.manipulation_detected:
            if invalidate:
                self.manipulation_detected = True
        return

