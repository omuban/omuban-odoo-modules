from odoo import models, fields, api
from datetime import timedelta

class EasySubscription(models.Model):
    _name = 'easy.subscription'
    _description = 'Data Langganan Client'
    _inherit = ['mail.thread']
    
    partner_id = fields.Many2one('res.partner', string="Client", required=True, tracking=True)
    product_id = fields.Many2one('product.product', string="Paket", required=True)
    end_date = fields.Date(string="Berakhir Pada", required=True, tracking=True)
    active = fields.Boolean(default=True)
    
    state = fields.Selection([
        ('active', 'Aktif'),
        ('expired', 'Habis')
    ], compute='_compute_state', store=True, tracking=True)

    @api.depends('end_date')
    def _compute_state(self):
        today = fields.Date.context_today(self)
        for sub in self:
            sub.state = 'active' if sub.end_date >= today else 'expired'

    def _sync_enrollment(self):
        """ 
        Dipanggil oleh Button B (atau AB/Cron).
        Fungsi: Menambahkan (Enroll) atau Menghapus (Unenroll) Client dari Kursus.
        """
        for sub in self:
            partner = sub.partner_id
            if not partner: continue
            
            # Kursus yang ditargetkan paket ini
            target_courses = sub.product_id.product_tmpl_id.sub_course_ids
            if not target_courses: continue

            # Cek status secara realtime
            is_active = sub.end_date >= fields.Date.context_today(sub)

            if is_active:
                # --- ACTION: ENROLL (GABUNG) ---
                for course in target_courses:
                    # Cek apakah sudah jadi member?
                    is_member = self.env['slide.channel.partner'].search_count([
                        ('channel_id', '=', course.id),
                        ('partner_id', '=', partner.id)
                    ])
                    if not is_member:
                        # Tambahkan Member via relation channel_partner_ids
                        # Command (4, id) = Link
                        course.sudo().write({'channel_partner_ids': [(4, partner.id)]})
                        
                        # (Opsional) Log di chatter
                        sub.message_post(body=f"User enrolled to course: {course.name}")
            
            else:
                # --- ACTION: UNENROLL (TENDANG) ---
                # Cek dulu: Apakah dia punya langganan LAIN yang aktif untuk kursus yang sama?
                # Kita tidak mau menendang user jika dia beli 2 paket yang irisannya sama.
                
                # Cari semua sub aktif milik user ini KECUALI sub ini
                other_active_subs = self.search([
                    ('partner_id', '=', partner.id),
                    ('end_date', '>=', fields.Date.context_today(sub)),
                    ('id', '!=', sub.id)
                ])
                
                # Kumpulkan semua kursus yang "Diamankan" oleh sub aktif lain
                safe_courses = other_active_subs.mapped('product_id.product_tmpl_id.sub_course_ids')

                for course in target_courses:
                    # Hanya tendang jika kursus ini TIDAK ada di daftar aman
                    if course not in safe_courses:
                         # Cek apakah masih member?
                        member_record = self.env['slide.channel.partner'].search([
                            ('channel_id', '=', course.id),
                            ('partner_id', '=', partner.id)
                        ])
                        if member_record:
                            # Hapus record membership
                            member_record.sudo().unlink()
                            
                            # (Opsional) Log
                            sub.message_post(body=f"Access revoked for course: {course.name}")

    @api.model
    def _cron_check_expiry(self):
        all_subs = self.search([])
        all_subs._compute_state()
        for sub in all_subs:
            sub._sync_enrollment()