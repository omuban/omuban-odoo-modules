from odoo import models, fields
from odoo.exceptions import UserError

class ContentPlatform(models.Model):
    _name = "content.platform"
    _description = "Content Platform"
    _rec_name = "name"

    name = fields.Char(string="Name", required=True)
    icon = fields.Image(string="Icon")
    state = fields.Selection(
        selection=[("enabled", "Enabled"), ("disabled", "Disabled")],
        string="State",
        required=True,
        default="enabled",
    )
    prompt_template = fields.Text(
        string="AI Prompt Template", 
        default="Buatlah konten sosial media yang menarik untuk {platform} berdasarkan topik berikut:\n\n{content}",
        help="Gunakan {content} sebagai placeholder teks sumber dan {platform} untuk nama platform."
    )

    def action_enable(self):
        for rec in self:
            rec.state = "enabled"
        return True

    def action_disable(self):
        for rec in self:
            rec.state = "disabled"
        return True
    
   