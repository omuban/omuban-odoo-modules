# -*- coding: utf-8 -*-
from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Mapping Produk Global (Tujuannya agar logic backend tidak "hardcoded" ID)
    cp_seat_product_id = fields.Many2one(
        'product.template', string="Global Seat Product",
        config_parameter='easy_subs_v2.seat_product_id',
        domain=[('cp_type', '=', 'seat')]
    )
    cp_setup_product_id = fields.Many2one(
        'product.template', string="Global Setup Product",
        config_parameter='easy_subs_v2.setup_product_id',
        domain=[('cp_type', '=', 'setup')]
    )

    # Konfigurasi Payment Gateway
    paddle_client_token = fields.Char("Paddle Client Token", config_parameter='easy_subs_v2.paddle_token')
    xendit_public_key = fields.Char("Xendit Public Key", config_parameter='easy_subs_v2.xendit_key')