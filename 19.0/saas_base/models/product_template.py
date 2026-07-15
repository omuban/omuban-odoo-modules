from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_saas_pkg = fields.Boolean(string="Is SaaS Product?", default=False)
    saas_duration = fields.Integer(string="Duration (Days)", default=30)
    saas_max_users = fields.Integer(string="Max Users Quota", default=10)
    saas_app_code = fields.Char(string="App Code Target")