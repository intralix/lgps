from odoo import api, models, fields, _

class FailureAttributionsList(models.Model):

    _name = 'lgps.failure_attributions_list'

    name = fields.Char(
        required=True,
        string=_("Attributions"),
    )

    code = fields.Char(
        string=_("Internal Code"),
        readonly=True,
        required=True,
        copy=False,
        default='New'
    )

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

        return super(FailureAttributionsList, self).copy(default)

    @api.model
    def create(self, vals):
        seq = self.env['ir.sequence'].next_by_code('lgps.failure_attributions_list') or _('New')
        vals['code'] = seq
        return super(FailureAttributionsList, self).create(vals)
