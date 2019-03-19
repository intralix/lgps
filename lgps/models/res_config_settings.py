# -*- coding: utf-8 -*-
from odoo import api, fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    channel_id = fields.Many2one('mail.channel', 'Default Channel',
                                  config_parameter='lgps.drop_device_wizard.default_channel',
                                  )

    def set_values(self):
        super(ResConfigSettings, self).set_values()

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        return res

