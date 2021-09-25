from odoo import api, models, fields, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)


class SaleAdvancePaymentInvCustomWizard(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    @api.multi
    def create_invoices(self):
        _logger.warning('%s', self)
        sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))
        _logger.warning('%s', sale_orders)
        stop = False

        for order in sale_orders:
            if not order.analytic_account_id:
                stop = True

        if stop:
            raise UserError(_("Al menos un pedido no tiene una cuenta analítica asignada.\nCompleta la información antes de crear la(s) factura(s)."))
        else:
            return super(SaleAdvancePaymentInvCustomWizard, self).create_invoices()




