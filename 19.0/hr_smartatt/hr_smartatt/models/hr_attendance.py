from odoo import fields, models

class HrAttendance(models.Model):
    """
    Mewarisi model hr.attendance untuk menambahkan relasi ke Work Location.
    """
    _inherit = 'hr.attendance'

    # === TAMBAHKAN FIELD BARU DI SINI ===
    work_location_id = fields.Many2one(
        'hr.work.location', 
        string='Work Location',
        help="The work location where the attendance was recorded."
    )
    attendance_proof_image = fields.Binary(
        string="Attendance Proof",
        help="A photo taken as proof of attendance."
    )
    # Extend in_mode (sudah ada sebelumnya)
    in_mode = fields.Selection(
        selection_add=[('mobile', 'Mobile')],
        ondelete={'mobile': 'set default'},
        string="Mode (Check-in)",
        readonly=True,
        default='manual'
    )

    # Extend out_mode (tambahkan pilihan 'mobile' atau opsi lain)
    out_mode = fields.Selection(
        selection_add=[('mobile', 'Mobile')],
        ondelete={'mobile': 'set default'},
        string="Mode (Check-out)",
        readonly=True,
        default='manual'
    )