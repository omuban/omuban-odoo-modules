{
    'name': 'White-Label Website: Remove or Customize "Powered by Odoo" Footer',
    'summary': 'Perfect for Agencies. Cleanly remove or completely rewrite the "Powered by Odoo" branding text from the website footer view via secure QWeb inheritance.',
    'version': '19.0.1.0.0',
    'category': 'Website',
    'author': 'Omuban',
    'license': 'OPL-1',
    'price': 15.00,
    'currency': 'USD',
    'depends': ['website'],
    'post_init_hook': 'post_init_hook',
    'data': [
        'views/footer.xml',
        'views/res_config_settings_views.xml',
    ],
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': False,
}