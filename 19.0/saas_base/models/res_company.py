from odoo import models, fields

class ResCompany(models.Model):
    _inherit = 'res.company'

    saas_status = fields.Selection([
        ('trial', 'Trial'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('blocked', 'Blocked')
    ], string="SaaS Status", index=True)
    
    expiry_date = fields.Date(string="Expiry Date", index=True)
    max_users = fields.Integer(string="Max Users Quota", default=1)
    saas_app_code = fields.Char(string="App Code", help="Identifier: smartatt, smartcrm, etc.")