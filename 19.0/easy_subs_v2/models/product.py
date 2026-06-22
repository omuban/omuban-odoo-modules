# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # Master switch yang Anda tambahkan
    is_saas_plan = fields.Boolean("Is CleanPresence SaaS Plan?", default=False)
    
    # Tetap sediakan is_easy_sub agar pencarian (search/domain) di controller tidak error
    is_easy_sub = fields.Boolean("Internal Legacy Flag", compute="_compute_is_easy_sub", store=True)

    cp_type = fields.Selection([
        ('core', 'Core Plan (Essential/Growth)'),
        ('addon', 'Add-on Feature (AI/etc)'),
        ('seat', 'Seat / User Access'),
        ('setup', 'Provisioning / Setup Fee'),
    ], string="CleanPresence Type", default='core')

    plan_group_code = fields.Char("Group Name", help="E.g. ESSENTIAL, GROWTH, TRIAL")
    sub_duration_days = fields.Integer("Duration (Days)", default=30)
    plan_code = fields.Char("Technical SKU Code")
    billing_cycle = fields.Selection([
        ('trial', 'Trial'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly')
    ], string="Billing Cycle", default='monthly')

    seat_limit = fields.Integer("Included Base Seats", default=5)
    
    beauty_price_ids = fields.One2many('easy.beauty.price', 'product_tmpl_id', string="Beauty Prices")
    cp_available_addon_ids = fields.One2many('easy.plan.addon.matrix', 'core_plan_id', string="Add-on Options")

    @api.depends('is_saas_plan', 'cp_type')
    def _compute_is_easy_sub(self):
        for rec in self:
            rec.is_easy_sub = rec.is_saas_plan or rec.cp_type in ['core', 'addon']

    def get_beauty_price_by_pricelist(self, pricelist_id):
        pricelist = self.env['product.pricelist'].sudo().browse(pricelist_id)
        match = self.beauty_price_ids.filtered(lambda x: x.currency_id == pricelist.currency_id)
        return match[0].fixed_price if match else self.list_price

# Class pendukung lainnya tetap seperti versi sebelumnya
class PlanAddonMatrix(models.Model):
    _name = 'easy.plan.addon.matrix'
    _description = 'Pricing Matrix for Addons'
    core_plan_id = fields.Many2one('product.template', ondelete='cascade')
    addon_product_id = fields.Many2one('product.template', domain=[('cp_type', '=', 'addon')])
    currency_id = fields.Many2one('res.currency', string="Currency", required=True)
    special_price = fields.Float("Fixed Special Price", required=True)

class EasyBeautyPrice(models.Model):
    _name = 'easy.beauty.price'
    _description = 'Beauty Pricing Matrix'
    product_tmpl_id = fields.Many2one('product.template', ondelete='cascade')
    currency_id = fields.Many2one('res.currency', string="Currency", required=True)
    fixed_price = fields.Float("Beauty Price (Fixed)", required=True)