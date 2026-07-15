from odoo import models, fields, api

class SaasWalletTransaction(models.Model):
    _name = 'saas.wallet.transaction'
    _description = 'SaaS Wallet Transaction Ledger'
    _order = 'create_date desc'

    name = fields.Char(string="Reference", required=True, readonly=True, default="/")
    partner_id = fields.Many2one('res.partner', string="Customer", required=True, index=True)
    amount = fields.Monetary(string="Amount", currency_field='currency_id')
    transaction_type = fields.Selection([
        ('in', 'Top-up / Refund'),
        ('out', 'Payment'),
        ('bonus', 'Bonus / Promo')
    ], string="Type", required=True)
    description = fields.Text(string="Description")
    notes = fields.Text(string="Technical Notes (JSON/Logs)")
    
    company_id = fields.Many2one('res.company', string="Company", required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code('saas.wallet.transaction') or '/'
        return super().create(vals_list)