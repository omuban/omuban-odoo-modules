# -*- coding: utf-8 -*-
from . import models

def post_init_hook(*args, **kwargs):
    """
    Bulletproof post_init_hook for Odoo 19.
    It will accept any number of arguments to avoid TypeError.
    """
    # In Odoo 19, the first argument is 'env'
    if args:
        env = args[0]
        
        # Log to server console so you can see it working
        print("--- FOOTER BRANDING: INSTALLING DEFAULTS ---")
        
        params = env['ir.config_parameter'].sudo()
        company_name = env.company.name or "Company"
        
        params.set_param('footer_branding_enabled', 'True')
        params.set_param('footer_branding_text', f'Copyright © Company name. Powered by {company_name}')