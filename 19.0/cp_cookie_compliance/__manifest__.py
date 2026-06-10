{
    'name': 'CleanPresence Cookie Consent',
    'version': '1.0',
    'category': 'Website',
    'summary': 'Simple, GDPR-aligned cookie banner for CleanPresence',
    'depends': ['website'],
    'data': [
        'views/templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'cp_cookie_compliance/static/src/css/cookie_style.css',
            'cp_cookie_compliance/static/src/js/cookie_manager.js',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}