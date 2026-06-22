import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

class SaasWorkspaceController(http.Controller):

    @http.route('/workspace/setup', type='json', auth='user', methods=['POST'], website=True)
    def setup_workspace(self, **post):
        user = request.env.user
        subdomain = post.get('subdomain', '').strip().lower()
        plan_id = int(post.get('plan_id', 0))
        company_name = post.get('company_name', '')
        extra_seats = int(post.get('additional_seats', 0))
        addons_dict = post.get('addons', {})  # Format: {product_template_id_str: {"p": price}}

        # 1. VALIDASI PROTEKSI (1 USER = 1 INSTANCE)
        existing = request.env['saas.tenant'].sudo().search([
            ('owner_id', '=', user.partner_id.id),
            ('state', 'not in', ['expired'])
        ], limit=1)
        
        if existing:
            return {'success': False, 'msg': f'Existing workspace found: {existing.name}'}

        plan = request.env['product.template'].sudo().browse(plan_id)
        if not plan.exists():
            return {'success': False, 'msg': 'Plan configuration mismatch.'}

        # 2. CREATE SAAS TENANT RECORD
        tenant = request.env['saas.tenant'].sudo().create({
            'name': subdomain,
            'company_name': company_name,
            'owner_id': user.partner_id.id,
            'plan_id': plan.id,
            'max_seats': getattr(plan, 'seat_limit', 0) + extra_seats,
            'state': 'provisioning' if plan.billing_cycle == 'trial' else 'pending_payment'
        })

        # --- CASE A: FREE TRIAL ---
        if plan.billing_cycle == 'trial':
            return {'success': True, 'gateway': 'free', 'redirect_url': f'/workspace/creating/{tenant.id}'}

        # --- CASE B: BERBAYAR (Generate Order Lines) ---
        get_param = request.env['ir.config_parameter'].sudo().get_param
        seat_p_id = int(get_param('easy_subs_v2.seat_product_id', 0))
        setup_p_id = int(get_param('easy_subs_v2.setup_product_id', 0))
        
        current_pricelist = request.website.get_current_pricelist()
        order_lines = []

        # Item 1: Base Plan
        base_product = request.env['product.product'].sudo().search([('product_tmpl_id', '=', plan.id)], limit=1)
        if base_product:
            order_lines.append((0, 0, {
                'product_id': base_product.id,
                'name': f"Presence Subscription: {plan.name}",
                'product_uom_qty': 1,
                'price_unit': plan.get_beauty_price_by_pricelist(current_pricelist.id) if hasattr(plan, 'get_beauty_price_by_pricelist') else plan.list_price
            }))

        # Item 2: Additional Seats (Jika Ada)
        if extra_seats > 0 and seat_p_id:
            # Perbaikan: Mencari di product.product berdasarkan product_tmpl_id dari config parameter
            seat_p = request.env['product.product'].sudo().search([('product_tmpl_id', '=', seat_p_id)], limit=1)
            if seat_p:
                seat_tmpl = seat_p.product_tmpl_id
                price_unit = seat_tmpl.get_beauty_price_by_pricelist(current_pricelist.id) if hasattr(seat_tmpl, 'get_beauty_price_by_pricelist') else seat_p.lst_price
                
                order_lines.append((0, 0, {
                    'product_id': seat_p.id,
                    'name': f"Additional Users Capacity ({extra_seats} seats)",
                    'product_uom_qty': extra_seats,
                    'price_unit': price_unit
                }))

        # Item 3: Addons (Dinamis dari Map)
        for addon_id_str, addon_data in addons_dict.items():
            try:
                addon_id = int(addon_id_str)
                addon_p = request.env['product.product'].sudo().search([('product_tmpl_id', '=', addon_id)], limit=1)
                if addon_p.exists():
                    order_lines.append((0, 0, {
                        'product_id': addon_p.id,
                        'name': f"Extension: {addon_p.name}",
                        'product_uom_qty': 1,
                        'price_unit': addon_data.get('p', 0.0)
                    }))
            except (ValueError, KeyError):
                continue

        # Item 4: Setup Fee
        if setup_p_id:
            setup_p = request.env['product.product'].sudo().search([('product_tmpl_id', '=', setup_p_id)], limit=1)
            if setup_p:
                setup_tmpl = setup_p.product_tmpl_id
                price_unit = setup_tmpl.get_beauty_price_by_pricelist(current_pricelist.id) if hasattr(setup_tmpl, 'get_beauty_price_by_pricelist') else setup_p.lst_price
                
                order_lines.append((0, 0, {
                    'product_id': setup_p.id,
                    'name': "Standard Platform Provisioning",
                    'product_uom_qty': 1,
                    'price_unit': price_unit
                }))

        # CREATE SALE ORDER
        order = request.env['sale.order'].sudo().create({
            'partner_id': user.partner_id.id,
            'is_cp_saas_order': True,
            'order_line': order_lines,
            'pricelist_id': current_pricelist.id,
        })

        # DECISION GATEWAY
        if order.currency_id.name == 'IDR':
            # Logic Xendit redirect link
            pay_url = self._get_xendit_invoice_url(order)
            return {'success': True, 'gateway': 'xendit', 'redirect_url': pay_url}
        else:
            # Logic Paddle info
            return {
                'success': True,
                'gateway': 'paddle',
                'order_id': order.id,
                'amount': order.amount_total,
                'currency': order.currency_id.name
            }

    def _get_xendit_invoice_url(self, order):
        # Placeholder method agar tidak error saat dipanggil di atas
        return f"/shop/payment/xendit/shortcut/{order.id}"