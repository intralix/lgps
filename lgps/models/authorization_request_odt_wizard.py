# -*- coding: utf-8 -*-
from datetime import timedelta
from odoo import api, models, fields, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class AuthorizationRequestODTWizard(models.TransientModel):
    _name = "lgps.authorization_request_odt_wizard"
    _description = "Authorizations for ODT in Warranty"

    def _default_odts(self):
        return self.env['repair.order'].browse(self._context.get('active_ids'))

    odt_ids = fields.Many2many(
        comodel_name='repair.order',
        string=_("ODT"),
        required=True,
        default=_default_odts,
    )

    requested_by = fields.Many2one(
        comodel_name='res.users',
        string=_("Requested by"),
        required=True,
        default=lambda s: s.env.uid,
    )

    request_comment = fields.Text(
        string=_("Operation Reason"),
        required=True,
    )

    last_warranty_date = fields.Date(
        string=_("Last warranty date"),
        required=True,
    )

    @api.multi
    def execute_authorization(self):
        if len(self._context.get('active_ids')) < 1:
            raise UserError(_('Select at least one record.'))

        active_model = self._context.get('active_model')
        active_records = self.env[active_model].browse(self._context.get('active_ids'))

        operation_log_comment = 'Se solicita autorización para garantía con la siguiente información:<br><br>'
        operation_log_comment += '<strong>Solicitador por: </strong> REQUEST_BY<br>'
        operation_log_comment += '<strong>Razón de la solicitud: </strong> REQUEST_COMMENT<br>'
        operation_log_comment += '<strong>Última fecha de garantía: </strong> LAST_WARRANTY_DATE<br>'

        for odt in active_records:
            if not odt.is_guarantee:
                raise UserError(_('This record does not have warranty check box checked'))

            # Estatus del Equipo como desinstalado
            #odt.write({ 'authorized_warranty': True })

            operation_log_comment = operation_log_comment.replace("REQUEST_BY", self.requested_by.name)
            operation_log_comment = operation_log_comment.replace("REQUEST_COMMENT", self.request_comment)
            operation_log_comment = operation_log_comment.replace("LAST_WARRANTY_DATE", self.last_warranty_date.strftime('%Y-%m-%d'))
            odt.write({
                    'is_guarantee': True,
                    'authorization_requested': True,
                    'authorized_warranty': 'waiting'
            })
            odt.message_post(body=operation_log_comment)

        return {}
