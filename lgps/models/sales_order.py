# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
import logging
_logger = logging.getLogger(__name__)


class SalesOrder(models.Model):
    _inherit = 'sale.order'

    title = fields.Char(
        string=_("Internal Title"),
    )
