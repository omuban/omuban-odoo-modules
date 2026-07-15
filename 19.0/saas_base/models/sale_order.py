# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_pay_with_wallet(self):
        """
        Melunasi Sales Order menggunakan saldo wallet partner.
        Fungsi ini memicu konfirmasi SO dan aktivasi SaaS.
        """
        self.ensure_one()
        partner = self.partner_id
        
        if partner.wallet_balance < self.amount_total:
            return False # Saldo tidak cukup, biarkan tetap Draft
            
        # 1. Potong Saldo Wallet
        partner.adjust_wallet(-self.amount_total, _("Payment for Order %s") % self.name)
        
        # 2. Konfirmasi Pesanan (Ini akan memicu _activate_paid_subscription yang sudah kita buat)
        self.action_confirm()
        
        # 3. (Opsional) Tandai sebagai lunas di log
        self.message_post(body=_("Order fully paid using Wallet Balance."))
        return True

    def _get_wallet_shortfall(self) -> float:
        """
        Helper untuk Midtrans: Menghitung berapa sisa yang harus dibayar 
        setelah dikurangi saldo wallet yang ada.
        """
        shortfall = self.amount_total - self.partner_id.wallet_balance
        return max(0.0, shortfall)