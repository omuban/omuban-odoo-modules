# -*- coding: utf-8 -*-
import json
from odoo import http
from odoo.http import request

class CleanPresenceMain(http.Controller):

    @http.route('/pricing', type='http', auth='public', website=True)
    def pricing_page(self, **kw):
        website = request.website
        
        # Penanganan Pricelist Safe Mode
        pl_id = request.session.get('website_sale_current_pl')
        if pl_id:
            current_pricelist = request.env['product.pricelist'].sudo().browse(pl_id)
        else:
            current_pricelist = website.pricelist_ids[:1] or request.env['product.pricelist'].sudo().search([], limit=1)

        # Ambil produk core SaaS (Urutan berdasarkan sequence website)
        plans = request.env['product.template'].sudo().search([
            ('is_saas_plan', '=', True), 
            ('cp_type', '=', 'core')
        ], order='website_sequence asc, id desc')
        
        plan_groups = {}
        for p in plans:
            code = (p.plan_group_code or 'Trial').upper()
            if code not in plan_groups:
                plan_groups[code] = {'monthly': False, 'yearly': False, 'trial': False}
            plan_groups[code][p.billing_cycle] = p

        # Mapping Produk Seat dan Setup Fee dari System Parameter
        param = request.env['ir.config_parameter'].sudo()
        setup_p = request.env['product.template'].sudo().browse(int(param.get_param('easy_subs_v2.setup_product_id', 0)))

        vals = {
            'plan_groups': plan_groups,
            'current_pricelist': current_pricelist,
            'is_logged_in': bool(request.session.uid),
            'setup_fee': float(setup_p.get_idr_price()) if setup_p.exists() else 0.0,
            'pricelists': request.env['product.pricelist'].sudo().search([('selectable', '=', True)]),
        }
        return request.render('easy_subs_v2.pricing_page_clean', vals)

    @http.route('/saas/check_subdomain', type='json', auth='public', website=True)
    def check_sub(self, subdomain):
        existing = request.env['saas.tenant'].sudo().search_count([('name', '=', subdomain.lower())])
        return {'available': existing == 0, 'msg': 'Siap dipakai!' if existing == 0 else 'Subdomain sudah ada.'}

    @http.route('/workspace/setup', type='json', auth='user', methods=['POST'], website=True)
    def setup_finish(self, **post):
        sub = post.get('subdomain')
        msg = f"Halo CleanPresence, saya order subdomain: {sub}. Mohon info tagihannya."
        wa_number = "6282333835683"
        wa_url = f"https://wa.me/{wa_number}?text={msg.replace(' ', '%20')}"
        return {'success': True, 'wa_url': wa_url, 'redirect_url': '/pricing'}
