from odoo import models, fields

class ContentProcessed(models.Model):
    _name = "content.processed"
    _description = "Processed Content"
    _rec_name = "content_resource_id"

    content_resource_id = fields.Many2one('content.resource', required=True, ondelete='cascade')
    platform_id = fields.Many2one('content.platform', required=True)
    generated_text = fields.Text("Generated Text", required=True)
    media_id = fields.Many2one('content.resource.media', string="Selected Media")
 