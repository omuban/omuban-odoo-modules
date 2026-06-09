from odoo import fields, models

class HrWorkLocation(models.Model):
    """
    Mewarisi model hr.work.location untuk menambahkan field koordinat.
    """
    _inherit = 'hr.work.location'

    latitude = fields.Float(
        string='Latitude', 
        digits=(10, 7),  # Presisi tinggi untuk koordinat geografis
        help="GPS Latitude of the work location."
    )
    longitude = fields.Float(
        string='Longitude', 
        digits=(10, 7), # Presisi tinggi untuk koordinat geografis
        help="GPS Longitude of the work location."
    )
    radius = fields.Integer(
        string='Valid Radius (meters)',
        default=50,
        help="The valid radius in meters from the central point for attendance."
    )