# File: models/dashboard.py
from odoo import models, api
from datetime import date, datetime, time
from datetime import timedelta

class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    @api.model
    def get_dashboard_data(self):
        """ Mengambil statistik untuk Dashboard OWL """
        today = date.today()
        start_day = datetime.combine(today, time.min)
        end_day = datetime.combine(today, time.max)

        # 1. Total Employees
        total_employees = self.env['hr.employee'].search_count([])

        # 2. Total Work Locations (BARU)
        total_locations = self.env['hr.work.location'].search_count([])

        # 3. Hadir Hari Ini (Check-in hari ini)
        attendance_today = self.search([
            ('check_in', '>=', start_day),
            ('check_in', '<=', end_day)
        ])
        present_employees = attendance_today.mapped('employee_id')
        present_count = len(present_employees)

        # 4. Belum Hadir
        absent_count = total_employees - present_count

        return {
            'total_employees': total_employees,
            'total_locations': total_locations,
            'present_count': present_count,
            'absent_count': absent_count,
        }
    @api.model
    def get_chart_data(self):
        today = date.today()
        dates = []
        present_percentages = [] # Ubah variabel penampung
        present_counts = []

        # Ambil total karyawan aktif saat ini sebagai pembagi
        total_employees = self.env['hr.employee'].search_count([])

        # Loop 7 hari ke belakang
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            start_day = datetime.combine(day, time.min)
            end_day = datetime.combine(day, time.max)
            
            # Hitung jumlah hadir
            attendance_count = self.search_count([
                ('check_in', '>=', start_day),
                ('check_in', '<=', end_day)
            ])
            
            # Hitung Persentase
            # Rumus: (Hadir / Total Karyawan) * 100
            if total_employees > 0:
                pct = (attendance_count / total_employees) * 100
            else:
                pct = 0

            dates.append(day.strftime('%d/%m'))
            present_percentages.append(round(pct, 1)) # Bulatkan 1 desimal
            present_counts.append(attendance_count)

            start_today = datetime.combine(today, time.min)
            end_today = datetime.combine(today, time.max)
            
            # Menggunakan read_group agar efisien
            location_groups = self.read_group(
                domain=[
                    ('check_in', '>=', start_today),
                    ('check_in', '<=', end_today),
                    ('work_location_id', '!=', False) # Pastikan field ini ada isinya
                ],
                fields=['work_location_id'],
                groupby=['work_location_id']
            )
            
            loc_labels = []
            loc_data = []
            
            for group in location_groups:
                # group['work_location_id'] formatnya biasanya (id, 'Name')
                location_name = group['work_location_id'][1] if group['work_location_id'] else 'Unknown'
                count = group['work_location_id_count']
                
                loc_labels.append(location_name)
                loc_data.append(count)
        return {
            'weekly_labels': dates,
            'weekly_data': present_percentages,
            'weekly_counts': present_counts, 
            # Data Donut Chart
            'location_labels': loc_labels,
            'location_data': loc_data,
        }