# -*- coding: utf-8 -*-
from odoo.http import request
from odoo.addons.auth_signup.controllers.main import AuthSignupHome

class SmartattSaaSController(AuthSignupHome):
    """
    Controller ini sekarang hanya fokus pada kustomisasi pendaftaran (Signup).
    Urusan belanja diserahkan sepenuhnya ke modul website_sale standar.
    """

    def _prepare_signup_values(self, qcontext):
        values = super()._prepare_signup_values(qcontext)
        values.update({
            'company_name': qcontext.get('company_name'),
            'company_address': qcontext.get('company_address'),
        })
        return values

    def do_signup(self, qcontext):
        res = super().do_signup(qcontext)
        if qcontext.get('company_name'):
            user = request.env.user
            # Buat Company baru untuk Tenant
            new_company = request.env['res.company'].sudo().create({
                'name': qcontext.get('company_name'),
                'street': qcontext.get('company_address'),
                'saas_status': 'trial',
            })
            # Hubungkan User ke Company tersebut
            user.sudo().write({
                'company_id': new_company.id,
                'company_ids': [(4, new_company.id)],
            })
        return res