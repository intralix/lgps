# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    lgps_default_channel_id = fields.Many2one(
        'mail.channel',
        string=_("Default Drop Channel"),
        config_parameter='lgps.device_wizard.drop_default_channel',
    )

    hibernate_channel_id = fields.Many2one(
        'mail.channel',
        string=_("Default Hibernate Channel"),
        config_parameter='lgps.hibernate_device_wizard.default_channel',
    )

    subscription_hibernate_product_id = fields.Many2one(
        'product.product',
        string=_("Default Hibernate Service"),
        domain=[
            ("recurring_invoice", "=", True)
        ],
        config_parameter='lgps.device_wizard.hibernate_default_service',
    )

    subscription_hibernate_commercial_id = fields.Many2one(
        'crm.team',
        string=_("Default Hibernate Commercial Team"),
        config_parameter='lgps.device_wizard.hibernate_commercial_default',
    )

    subscription_hibernate_user_id = fields.Many2one(
        'res.users',
        string=_("Default Hibernate Subscription User"),
        config_parameter='lgps.device_wizard.hibernate_user_default',
    )

    subscription_hibernate_stage_id = fields.Many2one(
        'sale.subscription.stage',
        string=_("Default Hibernate Subscription Stage"),
        config_parameter='lgps.device_wizard.hibernate_default_subscription_stage',
    )

    subscription_hibernate_stage_id_currents = fields.Many2one(
        'sale.subscription.stage',
        string=_("Default Hibernate Stage Current Subscriptions"),
        config_parameter='lgps.device_wizard.hibernate_current_subscription_stage',
    )

    subscription_hibernate_default_price_list_id = fields.Many2one(
        'product.pricelist',
        string=_("Default Hibernate Subscription Price List"),
        config_parameter='lgps.device_wizard.hibernate_default_price_list_id',
    )

    subscription_hibernate_template_id = fields.Many2one(
        'sale.subscription.template',
        string=_("Default Hibernate Template"),
        config_parameter='lgps.device_wizard.hibernate_default_subscription_template',
    )

    replacement_channel_id = fields.Many2one(
        'mail.channel',
        string=_("Default Replacements Channel"),
        config_parameter='lgps.device_wizard.replacement_default_channel',
    )

    substitution_channel_id = fields.Many2one(
        'mail.channel',
        string=_("Default Substitutions Channel"),
        config_parameter='lgps.device_wizard.substitution_default_channel',
    )

    repairs_default_price_list_id = fields.Many2one(
        'product.pricelist',
        string=_("Default Repairs Subscription Price List"),
        config_parameter='lgps.device_wizard.repairs_default_price_list_id',
    )

    add_reactivation_channel_id = fields.Many2one(
        'mail.channel',
        string=_("Default Add/Reactivation Channel"),
        config_parameter='lgps.add_reactivation_device_wizard.default_channel',
    )

    def set_values(self):
        super(ResConfigSettings, self).set_values()

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        return res

