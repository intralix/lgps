from odoo import api, models, fields, _

class FailureRootProblemList(models.Model):

    _name = 'lgps.failure_root_problem_list'

    name = fields.Char(
        required=True,
        string=_("Root Problem"),
    )

    code = fields.Char(
        string=_("Internal Code"),
        readonly=True,
        required=True,
        copy=False,
        default='New'
    )

    # Si la linea esta ocupada o no
    invalidate = fields.Boolean(
        default=False,
        string=_("Void Warranty"),
    )

    failure_components_list_id = fields.Many2one(
        comodel_name="lgps.failure_components_list",
        string=_("Components Category"),
        ondelete='set null',
        required=True
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

        return super(FailureRootProblemList, self).copy(default)

    @api.model
    def create(self, vals):
        seq = self.env['ir.sequence'].next_by_code('lgps.failure_root_problem_list') or _('New')
        vals['code'] = seq
        return super(FailureRootProblemList, self).create(vals)
