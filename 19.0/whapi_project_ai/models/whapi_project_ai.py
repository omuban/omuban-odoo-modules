from odoo import api, fields, models, _
import logging

_logger = logging.getLogger(__name__)

class WhapiProjectAI(models.Model):
    _inherit = 'whapi.message'
    _description = 'Integration of WhatsApp + Project Management + Google Gemini AI'

    project_id = fields.Many2one(
        comodel_name='project.project',
        string='Project',
        ondelete='set null',
        help='Project tujuan ketika membuat project.task dari pesan',
        default=lambda self: self._get_default_project()
    )


    @api.model
    def _get_default_project(self):
        """Return the project.record named 'Default'. If not exists, create it."""
        env = self.env
        try:
            proj = env['project.project'].sudo().search([('name', '=', 'WhatsApp')], limit=1)
            if proj:
                return proj.id
            # create the default project if not found (if model exists)
            if 'project.project' in env:
                proj = env['project.project'].sudo().create({'name': 'WhatsApp'})
                return proj.id
        except Exception as e:
            _logger.warning("Could not get/create default project 'Default': %s", e)
        return False


    def action_create_task(self):
        """Manual action to create a task from this message record."""
        self.ensure_one()
        task_vals = {
            'name': (self.sender or self.name or 'Message from WHAPI')[:256],
            'description': self.formatted_text or self.text or '',
        }
        if self.project_id:
            task_vals['project_id'] = self.project_id.id
        try:
            if 'project.task' in self.env:
                # create task with sudo to avoid access rights issues
                task = self.env['project.task'].sudo().create(task_vals)
                return task
            else:
                _logger.warning("project.task model not available - cannot create task")
                return False
        except Exception as e:
            _logger.error('Failed to create task from message %s: %s', self.id, e)
            return False
