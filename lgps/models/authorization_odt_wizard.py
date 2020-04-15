# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from odoo.exceptions import UserError


class AuthorizationODTWizard(models.TransientModel):
    _name = "lgps.authorization_odt_wizard"
    _description = "Authorizations for ODT in Warranty"

    def _default_odts(self):
        return self.env['repair.order'].browse(self._context.get('active_ids'))

    odt_ids = fields.Many2many(
        comodel_name='repair.order',
        string=_("ODT"),
        required=True,
        default=_default_odts,
    )

    status = fields.Selection(
        selection=[
            ("rejected", _("Rechazada")),
            ("authorized", _("Autorizada")),
        ],
        default="rejected",
        string=_("Status"),
    )

    request_comment = fields.Text(
        string=_("Operation Reason"),
        required=True,
    )

    @api.multi
    def execute_authorization(self):
        if len(self._context.get('active_ids')) < 1:
            raise UserError(_('Select at least one record.'))

        active_model = self._context.get('active_model')
        active_records = self.env[active_model].browse(self._context.get('active_ids'))

        operation_log_comment = 'STATUS<br><br>'
        operation_log_comment += '<strong>Comentarios: </strong> REQUEST_COMMENT<br>'

        for odt in active_records:
            if not odt.is_guarantee:
                raise UserError(_('This record does not have warranty check box checked'))
            if not odt.authorization_requested:
                raise UserError(_('This record does not have and authorization request'))

            if odt.authorized_warranty == 'waiting':
                if self.status == 'rejected':
                    str_status = 'Rechazada'
                    is_guarantee = False
                else:
                    str_status = 'Autorizada'
                    is_guarantee = True

                odt.write({
                    'authorized_warranty': self.status,
                    'is_guarantee': is_guarantee
                })

                operation_log_comment = operation_log_comment.replace("STATUS", str_status)
                operation_log_comment = operation_log_comment.replace("REQUEST_COMMENT", self.request_comment)
                odt.message_post(body=operation_log_comment)
            else:
                raise UserError(
                    _("Repair does not have an authorization request")
                )

        return {}
