# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    footer_branding_text = fields.Char(string="Footer Branding Text")
    footer_branding_enabled = fields.Boolean(string="Enable Footer Branding")

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            'footer_branding_enabled', str(self.footer_branding_enabled))
        self.env['ir.config_parameter'].sudo().set_param(
            'footer_branding_text', self.footer_branding_text or '')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        res.update(
            footer_branding_enabled=params.get_param('footer_branding_enabled') == 'True',
            footer_branding_text=params.get_param('footer_branding_text'),
        )
        return res