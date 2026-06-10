from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    footer_branding_text = fields.Char(
        string="Footer Branding Text",
        config_parameter="selstudio.footer_branding_text",
        default="Powered by CV. Sel Studio",
    )

    footer_branding_enabled = fields.Boolean(
        string="Enable Custom Footer Branding",
        config_parameter="selstudio.footer_branding_enabled",
        default=True,
    )
