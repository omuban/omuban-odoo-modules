{
    'name': 'SaaS Front-End UI',
    'version': '19.0.1.0.0',
    'category': 'Website',
    'summary': 'Professional Pricing Cards, Custom Signup, and Portal Info',
    'author': 'SmartAtt Team',
    'depends': ['saas_base', 'website_sale', 'auth_signup'],
    'data': [
        'views/website_shop_price_logic.xml',  # Load logika harga
        'views/website_shop_actions.xml',      # Load tombol aksi
        'views/website_shop_layout.xml',       # Load layout utama
        'views/website_product_page.xml',
        'views/portal_templates.xml',
    ],
    'installable': True,
    'license': 'LGPL-3',
}