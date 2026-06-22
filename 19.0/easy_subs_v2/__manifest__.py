# -*- coding: utf-8 -*-
{
    'name': 'CleanPresence SaaS Engine V2',
    'version': '2.0',
    'category': 'SaaS',
    'summary': 'Modular SaaS Infrastructure (Paddle & Xendit Ready)',
    'author': 'LawHub Team',
    'depends': [
        'website', 
        'website_sale', 
        'sale_management', 
        'product', 
        'mail'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_view.xml',
        'views/product_view.xml',
        'views/saas_tenant_view.xml',
        'views/pricing_templates.xml',       # <--- PASTIKAN ADA INI
        'views/provisioning_templates.xml',  # <--- PASTIKAN ADA INI
        'views/legal_templates.xml',         # <--- PASTIKAN ADA INI
        'data/mail_template_data.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}