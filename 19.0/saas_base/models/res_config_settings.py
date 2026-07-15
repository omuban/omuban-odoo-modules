from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    saas_trial_product_id = fields.Many2one(
        'product.product', 
        string="Trial Product Reference",
        domain="[('is_saas_pkg', '=', True)]",
        config_parameter='saas_base.trial_product_id'
    )
    