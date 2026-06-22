# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import timedelta

class SaasTenant(models.Model):
    _name = 'saas.tenant'
    _description = 'Master Record for CleanPresence Tenants'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char("Subdomain", required=True, tracking=True)
    company_name = fields.Char("Organization Name", required=True, tracking=True)
    owner_id = fields.Many2one('res.partner', string="Owner (Partner)", required=True, tracking=True)
    plan_id = fields.Many2one('product.template', string="SaaS Plan", required=True, tracking=True)
    max_seats = fields.Integer("Seats Capacity", default=1, tracking=True)
    
    state = fields.Selection([
        ('draft', 'Pending'),
        ('pending_payment', 'Awaiting Payment'),
        ('provisioning', 'Deploying'),
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('expired', 'Expired')
    ], string="Status", default='draft', tracking=True)

    start_date = fields.Date("Start Date", default=fields.Date.context_today)
    expiration_date = fields.Date("Valid Until", tracking=True)
    database_name = fields.Char("PostgreSQL DB Name", readonly=True)
    
    # Field yang tadinya menyebabkan error
    is_trial = fields.Boolean("Trial Instance?", compute="_compute_is_trial", store=True)

    @api.depends('plan_id.billing_cycle')
    def _compute_is_trial(self):
        for rec in self:
            rec.is_trial = rec.plan_id.billing_cycle == 'trial' if rec.plan_id else False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'name' in vals:
                # Membersihkan nama subdomain dari spasi/karakter aneh
                clean_name = "".join(filter(lambda x: x.isalnum(), vals['name'])).lower()
                vals['database_name'] = f"clean_{clean_name}"
            
            # Otomatisasi tanggal kadaluarsa berdasarkan plan jika belum diisi
            if 'plan_id' in vals and not vals.get('expiration_date'):
                plan = self.env['product.template'].browse(vals['plan_id'])
                if plan.exists():
                    duration = 7 if plan.billing_cycle == 'trial' else (365 if plan.billing_cycle == 'yearly' else 30)
                    vals['expiration_date'] = fields.Date.today() + timedelta(days=duration)
                    
        return super(SaasTenant, self).create(vals_list)