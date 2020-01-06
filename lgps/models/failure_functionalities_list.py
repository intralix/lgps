from odoo import api, models, fields, _

class FailureFunctionalitiesList(models.Model):

    _name = 'lgps.failure_functionalities_list'

    name = fields.Char(
        required=True,
        string=_("Functionalities"),
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

        return super(FailureFunctionalitiesList, self).copy(default)
