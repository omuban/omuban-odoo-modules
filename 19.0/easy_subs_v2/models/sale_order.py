# -*- coding: utf-8 -*-
from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # Menandai apakah SO ini berasal dari SaaS Wizard
    is_cp_saas_order = fields.Boolean("CleanPresence SaaS Order", default=False)
    
    # Simple workflow: Draft (Belum Bayar) -> Paid (Sudah Lunas)
    cp_state = fields.Selection([
        ('draft', 'Awaiting Payment'),
        ('paid', 'Active / Fully Paid')
    ], string="Subscription Status", default='draft', tracking=True)

    def action_saas_payment_success(self):
        """ 
        PENTING: Fungsi ini dipanggil oleh Webhook (Paddle/Xendit) 
        atau manual oleh admin jika ingin bypass.
        """
        for order in self:
            order.action_confirm() # Confirm SO
            invoice = order._create_invoices()
            invoice.action_post() # Post Invoice
            # Disini nanti tambahkan logic record payment agar residual = 0
            order.write({'cp_state': 'paid'})
            
            # Hubungkan kembali ke record tenant untuk merubah statusnya menjadi 'provisioning'
            tenant = self.env['saas.tenant'].sudo().search([('owner_id', '=', order.partner_id.id)], limit=1)
            if tenant:
                tenant.write({'state': 'provisioning'})
        return True