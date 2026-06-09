import json
import logging
import base64
from odoo import http, fields
from odoo.http import request, Response

_logger = logging.getLogger(__name__)

class SmartAttendanceFrontend(http.Controller):
    @http.route('/smartatt', type='http', auth='public', website=True, sitemap=False)
    def index(self, **kw):
        """
        Controller utama untuk frontend Smart Attendance.
        Memvalidasi bahwa pengguna yang login adalah seorang karyawan.
        """
        user = request.env.user
        
        # Cek jika pengguna belum login (masih user publik)
        if user._is_public():
            # Jika ada pesan error dari redirect (misal: access_denied)
            error_message = "Anda tidak memiliki hak akses sebagai karyawan." if kw.get('error') == 'access_denied' else False
            render_values = {
                'is_logged_in': False,
                'error_message': "Anda tidak memiliki hak akses." if kw.get('error') == 'access_denied' else None
            }
            return request.render("hr_smartatt.home", render_values)

        # Jika pengguna sudah login, cari relasi ke hr.employee
        # Kita cari berdasarkan user_id di model hr.employee
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)

        if not employee:
            # Jika tidak ada relasi karyawan, logout pengguna dan redirect dengan pesan error
            request.session.logout(keep_db=True)
            # Redirect ke halaman login dengan flag error
            return request.redirect('/smartatt?error=access_denied')

        render_values = {
            'is_logged_in': True,
            'user_name': employee.name,
            'employee_id': employee.id,
            # Tambahkan data departemen, jabatan, dan URL avatar
            'employee_department': employee.department_id.name or 'N/A',
            'employee_job_title': employee.job_id.name or 'N/A',
            # Membuat URL gambar avatar karyawan
            'employee_avatar_url': f"/web/image/hr.employee/{employee.id}/avatar_128",
            'error_message': None,
        }
        return request.render("hr_smartatt.home", render_values)
    
    @http.route('/smartatt/get_employee_data', type='json', auth='user')
    def get_employee_data(self):
        """
        Endpoint RPC untuk mengambil data karyawan yang sedang login.
        """
        #employee = request.env['hr.employee'].search([('user_id', '=', request.session.uid)], limit=1)
        employee = request.env['hr.employee'].sudo().search([
                ('user_id', '=', request.session.uid)
            ], limit=1)
        if employee:
            # Jika ditemukan, kembalikan datanya.
            # Odoo akan otomatis membungkusnya dalam format {"result": ...}
            return {
                'id': employee.id,
                'name': employee.name,
                'department': employee.department_id.name or 'N/A',
                'job_title': employee.job_id.name or 'N/A',
                'avatar_url': f"/smartatt/avatar/{employee.id}",
            }
        else:
            # Jika tidak ada karyawan yang terkait, kembalikan False.
            # Odoo akan membungkusnya menjadi {"result": false}
            return False
        
    @http.route('/smartatt/avatar/<int:employee_id>', type='http', auth='user')
    def get_smart_avatar(self, employee_id):
        """
        Mengambil avatar dengan hak akses admin (sudo), 
        sehingga user biasa tetap bisa melihat gambarnya.
        """
        # 1. Cari record dengan sudo()
        employee = request.env['hr.employee'].sudo().browse(employee_id)
        
        # 2. Cek apakah record ada dan field gambar terisi
        # avatar_128 adalah field standar Odoo (binary)
        if employee.exists() and employee.avatar_128:
            image_base64 = employee.avatar_128
            
            # 3. Decode base64 menjadi binary stream
            try:
                image_data = base64.b64decode(image_base64)
            except Exception:
                return request.not_found()

            # 4. Return sebagai respons gambar
            headers = [
                ('Content-Type', 'image/png'),
                ('Content-Length', len(image_data)),
                ('Cache-Control', 'max-age=3600, public') # Opsional: cache 1 jam biar cepat
            ]
            return request.make_response(image_data, headers)
        
        # 5. Jika tidak ada gambar, return 404 atau placeholder default Odoo
        # Opsi A: Return 404 (Browser akan menampilkan gambar pecah)
        # return request.not_found()
        
        # Opsi B: Redirect ke placeholder bawaan Odoo (Lebih rapi)
        return request.redirect('/web/static/img/placeholder.png')
    
    @http.route('/smartatt/get_attendance_history', type='json', auth='user')
    def get_attendance_history(self, limit=30):
        """
        Endpoint untuk mengambil riwayat absensi karyawan yang sedang login.
        """
        employee = request.env['hr.employee'].sudo().search([
            ('user_id', '=', request.session.uid)
        ], limit=1)

        if not employee:
            return []

        # Ambil record absensi, urutkan dari yang terbaru
        attendances = request.env['hr.attendance'].sudo().search_read(
            [('employee_id', '=', employee.id)],
            fields=['id', 'check_in', 'check_out', 'worked_hours', 'work_location_id'], # Tambahkan work_location_id
            order='check_in desc', 
            limit=limit
        )

        # Data sudah dalam format list of dict, tidak perlu loop manual
        for att in attendances:
            # Konversi waktu ke format string ISO
            if att.get('check_in'):
                att['check_in'] = att['check_in'].isoformat() + 'Z'
            if att.get('check_out'):
                att['check_out'] = att['check_out'].isoformat() + 'Z'

            # Ubah data relasi Many2one (ID, Nama) menjadi hanya Nama
            if att.get('work_location_id'):
                # att['work_location_id'] akan berisi [id, "Nama Lokasi"]
                att['work_location_name'] = att['work_location_id'][1]
            else:
                att['work_location_name'] = 'N/A' # Jika tidak ada lokasi
            del att['work_location_id'] # Hapus field lama agar tidak membingungkan

            # Bulatkan worked_hours
            att['worked_hours'] = round(att.get('worked_hours', 0), 1)
            
        return attendances

    @http.route('/smartatt/get_work_locations', type='json', auth='user')
    def get_work_locations(self):
        """
        Endpoint untuk mengambil daftar lokasi kerja yang aktif.
        """
        # Kita hanya mengambil lokasi kerja yang memiliki koordinat
        # dan radius yang valid (lebih besar dari nol).
        # Ini mencegah lokasi yang belum selesai dikonfigurasi muncul di frontend.
        locations = request.env['hr.work.location'].sudo().search([
            ('latitude', '!=', False),
            ('longitude', '!=', False),
            ('radius', '>', 0)
        ])

        # Menggunakan list comprehension untuk cara yang lebih singkat dan Pythonic
        locations_data = [{
            'id': loc.id,
            'name': loc.name,
            'latitude': loc.latitude,
            'longitude': loc.longitude,
            'radius': loc.radius,
        } for loc in locations]
        
        # Odoo akan otomatis membungkusnya dalam {"result": [...]}
        return locations_data
    
    @http.route('/smartatt/submit_check_in', type='json', auth='user', methods=['POST'], csrf=False)
    def submit_check_in(self, **kwargs):
        # Langkah kunci: Baca raw body JSON secara manual (paling aman untuk plain JSON POST)
        try:
            raw_body = request.httprequest.data.decode('utf-8')
            _logger.info(f"Raw body received: {raw_body}")

            payload = json.loads(raw_body)
            _logger.info(f"Parsed payload: {payload}")

        except json.JSONDecodeError as e:
            _logger.error(f"Invalid JSON body: {e}")
            return {
                'status': 'error',
                'code': 400,
                'message': "Invalid JSON format in request body"
            }
        except Exception as e:
            _logger.error(f"Error reading body: {e}")
            return {
                'status': 'error',
                'code': 400,
                'message': "Cannot read request body"
            }

        # Ambil data dari payload
        location_id = payload.get('location_id')
        image_data = payload.get('image_data')
        user_latitude = payload.get('user_latitude')
        user_longitude = payload.get('user_longitude')

    

        # Validasi (sudah disesuaikan agar lebih toleran terhadap tipe data)
        required = ['location_id', 'image_data', 'user_latitude', 'user_longitude']
        missing = [k for k in required if k not in payload or payload[k] is None]
        invalid = []

        try:
            int(location_id)  # pastikan bisa di-cast ke int
        except (TypeError, ValueError):
            invalid.append('location_id')

        if not image_data or not isinstance(image_data, str) or len(image_data) < 100:
            invalid.append('image_data')

        try:
            float(user_latitude)
        except (TypeError, ValueError):
            invalid.append('user_latitude')

        try:
            float(user_longitude)
        except (TypeError, ValueError):
            invalid.append('user_longitude')

        if missing or invalid:
            error_msg = f"Missing: {', '.join(missing)} | Invalid: {', '.join(invalid)}"
            _logger.warning(f"[CHECK-IN] Validation failed: {error_msg}")
            return {
                'status': 'error',
                'code': 400,
                'message': f"Bad Request: {error_msg}",
                'received_keys': list(payload.keys())
            }

        # Lanjut proses seperti sebelumnya (cari employee, proses image, create attendance)
        employee = request.env['hr.employee'].sudo().search([
            ('user_id', '=', request.env.user.id)
        ], limit=1)

        if not employee:
            return {'status': 'error', 'code': 404, 'message': "Employee not found"}

        try:
            # Proses image base64
            if not image_data.startswith('data:image'):
                raise ValueError("Invalid image format (must be data URI base64)")

            _, encoded = image_data.split(',', 1)
            image_b64 = encoded.strip()
            base64.b64decode(image_b64, validate=True)  # validasi

            attendance_vals = {
                'employee_id': employee.id,
                'check_in': fields.Datetime.now(),
                'work_location_id': int(location_id),
                'attendance_proof_image': image_b64,
                'in_mode': 'mobile',
                'in_latitude': float(user_latitude),
                'in_longitude': float(user_longitude),
            }

            new_attendance = request.env['hr.attendance'].sudo().create(attendance_vals)

            return {
                'status': 'success',
                'message': f"Check-in successful at {new_attendance.work_location_id.name or 'N/A'}",
                'attendance_id': new_attendance.id,
            }

        except Exception as e:
            _logger.error(f"[CHECK-IN] Error processing: {e}", exc_info=True)
            return {'status': 'error', 'code': 500, 'message': "Internal error"}
    
    @http.route('/smartatt/submit_check_out', type='json', auth='user', methods=['POST'], csrf=False)
    def submit_check_out(self, **kwargs):
        import json
        try:
            # ==== READ JSON BODY (DO NOT USE request.jsonrequest!) ====
            raw_body = request.httprequest.data.decode("utf-8")
            
            payload = json.loads(raw_body)
          
            attendance_id = payload.get('attendance_id')
            out_latitude = payload.get('out_latitude')
            out_longitude = payload.get('out_longitude')
            # Validation
            if not attendance_id or out_latitude is None or out_longitude is None:
                _logger.error(f"[CHECK-OUT] Validation failed: attendance_id={attendance_id}, out_latitude={out_latitude}, out_longitude={out_longitude}")
                return {'status': 'error', 'message': 'Missing required parameters.'}
            attendance = request.env['hr.attendance'].sudo().browse(int(attendance_id))
            if not attendance or not attendance.exists():
                _logger.error(f"[CHECK-OUT] Attendance not found: attendance_id={attendance_id}")
                return {'status': 'error', 'message': 'Attendance record not found.'}

            # Update checkout record
            attendance.write({
                'check_out': fields.Datetime.now(),
                'out_latitude': out_latitude,
                'out_longitude': out_longitude,
                'out_mode': 'mobile',
            })
            _logger.info(f"[CHECK-OUT] Success: attendance_id={attendance.id}")
            return {'status': 'success', 'message': 'Check-out successful.', 'attendance_id': attendance.id}
        except Exception as e:
            _logger.error(f"[CHECK-OUT] Error: {e}", exc_info=True)
            return {'status': 'error', 'message': "An error occurred during check-out."}