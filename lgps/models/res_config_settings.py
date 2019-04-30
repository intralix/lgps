# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    channel_id = fields.Many2one(
        'mail.channel',
        string=_("Default Drop Channel"),
        config_parameter='lgps.drop_device_wizard.default_channel',
    )

    hibernate_channel_id = fields.Many2one(
        'mail.channel',
        string=_("Default Hibernate Channel"),
        config_parameter='lgps.hibernate_device_wizard.default_channel',
    )

    suscription_hibernate_product_id = fields.Many2one(
        'product.product',
        string=_("Default Hibernate Service"),
        domain=[
            ("recurring_invoice", "=", True)
        ],
        config_parameter='lgps.hibernate_device_wizard.default_service',
    )

    suscription_hibernate_stage_id = fields.Many2one(
        'sale.subscription.stage',
        string=_("Default Hibernate Stage"),
        config_parameter='lgps.hibernate_device_wizard.default_subscription_stage',
    )

    suscription_hibernate_template_id = fields.Many2one(
        'sale.subscription.template',
        string=_("Default Hibernate Template"),
        config_parameter='lgps.hibernate_device_wizard.default_subscription_template',
    )

    def set_values(self):
        super(ResConfigSettings, self).set_values()

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        return res

