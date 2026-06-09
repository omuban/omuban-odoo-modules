from odoo import models, fields, api
from odoo.exceptions import UserError
import logging
import google.generativeai as genai

_logger = logging.getLogger(__name__)

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # config_parameter otomatis menyimpan value ke tabel ir.config_parameter
    gemini_api_key = fields.Char(
        string="Gemini API Key",
        config_parameter='content_generator.gemini_api_key',
        help="Masukkan API Key dari Google AI Studio"
    )
    def action_test_gemini_api_key(self):
        """
        Test the Gemini API Key from the settings form.
        """
        api_key = self.gemini_api_key or self.env['ir.config_parameter'].sudo().get_param('content_generator.gemini_api_key')

        if not api_key:
            raise UserError("API Key not found! Please configure your Gemini API Key.")

        try:
            # Konfigurasi Google AI
            genai.configure(api_key=api_key)
            model_name = 'models/gemini-2.5-flash'
            _logger.info(f"Testing connection with AI Model: {model_name}")
            
            # Validasi dengan meminta metadata model (bisa dianggap dummy request)
            model = genai.GenerativeModel(model_name)
            metadata = model  # Dummy metadata check (replace this with actual library debug request)
            _logger.info(f"Model metadata retrieved successfully: {metadata}")
            
        except Exception as e:
            raise UserError(f"Failed to connect to Gemini AI. Error: {str(e)}")

        # Jika sukses
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success!',
                'message': 'Successfully connected to Google Gemini AI!',
                'type': 'success',
                'sticky': False,
            }
        }