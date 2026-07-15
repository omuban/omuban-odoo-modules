# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ResPartner(models.Model):
    _inherit = 'res.partner'

    wallet_balance = fields.Monetary(
        string="Wallet Balance", 
        currency_field='currency_id', 
        default=0.0,
        tracking=True # Muncul di log jika berubah
    )

    def adjust_wallet(self, amount: float, transaction_type: str, description: str, notes: str = False):
        for partner in self:
            # 1. Wajib buat riwayat transaksi
            self.env['saas.wallet.transaction'].sudo().create({
                'partner_id': partner.id,
                'amount': amount,
                'transaction_type': transaction_type,
                'description': description,
                'notes': notes,
                'company_id': partner.company_id.id or self.env.company.id
            })
            # 2. Update saldo
            partner.sudo().write({'wallet_balance': partner.wallet_balance + amount})