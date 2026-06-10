{
    "name": "WhatsApp Integration",
    "version": "1.0.1",
    "author": "OMUBAN",
    "category": "Tools",
    "summary": "Receive WhatsApp messages into Odoo",
    "depends": ["base"],
    "data": [
        "security/ir.model.access.csv",
        "data/whapi_sequence.xml",        
        "views/whapi_views.xml",    
    ],
    'assets': {
        'web.assets_backend': [
            '/whapi_cloud_fixed/static/src/css/whapi_list.css',
        ],
    },

    "installable": True,
    "application": True,
    "auto_install": False,
}
