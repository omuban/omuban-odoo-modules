from odoo import models, fields

class ContentResourceMedia(models.Model):
    _name = 'content.resource.media'
    _description = 'Content Resource Media'
    _order = 'sequence, id' # Untuk bisa diurutkan nanti

    name = fields.Char(string='Description', required=True)
    file = fields.Image(string='File', required=True)
    sequence = fields.Integer(default=10)

    # Relasi Many2one ke model induk
    content_resource_id = fields.Many2one(
        'content.resource', 
        string='Content Resource', 
        required=True, 
        ondelete='cascade' # Jika resource dihapus, media ikut terhapus
    )