/** @odoo-module **/
import { Component, xml, onWillStart,onMounted,onWillUnmount, useState, useComponent,useRef } from "@odoo/owl";
function workedHoursStr(hours) {
    if (typeof hours !== 'number' || isNaN(hours)) return '00:00';
    const h = Math.floor(hours);
    const m = Math.round((hours - h) * 60);
    return `${h.toString().padStart(2,'0')}:${m.toString().padStart(2,'0')}`;
}
export class Dashboard extends Component {
    static props = ["employee", "onNavigate"];
    static template = xml`
       <div class="dashboard-container">
       <!-- CHECKOUT CONFIRMATION POPUP -->
            <div t-if="state.showCheckoutConfirm" class="modal-backdrop-custom">
                <div class="modal-confirm-custom">
                    <div class="modal-content">
                        <h4>Checkout Confirmation</h4>
                        <p>Are you sure you want to check out now?</p>
                        <div class="mt-3 d-flex justify-content-end gap-2">
                            <button class="btn btn-outline-secondary" t-on-click="() => { this.state.showCheckoutConfirm = false }">Cancel</button>
                            <button class="btn btn-danger"
                                    t-on-click="doCheckoutNow"
                                    t-att-disabled="state.isSubmitting">
                                <span t-if="state.isSubmitting" class="spinner-border spinner-border-sm me-2"/>
                                Checkout
                            </button>
                        </div>
                    </div>
                </div>
            </div>
            <div t-if="state.toast" class="custom-toast" t-att-class="state.toast.type">
                <i class="fa" t-att-class="state.toast.type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle'" />
                <span t-esc="state.toast.message"/>
            </div>
          <div class="dashboard-bg-header"></div>
          
           <header class="dashboard-top-header d-flex justify-content-between align-items-center">
             <!-- Left: Avatar -->
             <img t-att-src="props.employee.avatarUrl" class="profile-avatar" alt="Avatar"/>

             <!-- Centre: Name & Job Title -->
             <div class="text-white mx-3 flex-grow-1">
                <h5 class="fw-bold mb-0" t-esc="props.employee.name"/>
                <p class="mb-0 opacity-75" t-esc="props.employee.jobTitle"/>
             </div>

             <!-- Right: Notification Button -->
             <button class="btn btn-icon text-white">
                <i class="fa fa-bell fa-lg"/>
             </button>
          </header>

          <!-- Main Content (Cards) -->
          <main class="dashboard-content-wrapper">
             <!-- Main Check-in Card -->
             <!-- Main Working Card -->
            <section class="checkin-card text-center">
                <t t-if="state.isWorking">
                    <h2 class="fw-bold mb-2 text-success">
                        <i class="fa fa-briefcase me-2"/> WORKING
                    </h2>
                    <div class="working-timer mb-1">
                        <h1 class="main-clock" t-esc="state.workingTimer || '00:00:00'"/> 
                    </div>
                    <p class="main-date mb-3" t-esc="state.currentDate"/>
                    <button class="btn btn-danger btn-lg px-5 shadow" t-on-click="() => { this.state.showCheckoutConfirm = true }" style="font-size:1.3rem; font-weight:600;">
                        <i class="fa fa-sign-out-alt me-2"/>Check Out
                    </button>
                    <!-- Additional info: location & check-in time if needed -->
                    <div class="working-info mt-3" t-if="state.activeAttendance">
                        <div>
                            <i class="fa fa-map-marker me-1"/><span t-esc="state.activeAttendance.location"/>
                        </div>
                        
                    </div>
                    <p class="working-subtext mt-3">Don't forget to check out when you're done!</p>
                </t>
                <t t-else="">
                    <h1 class="main-clock" t-esc="state.timeDisplay.time"/>
                    <p class="main-clock-ampm" t-esc="state.timeDisplay.ampm"/>
                    <p class="main-date" t-esc="state.currentDate"/>
                    <button class="btn-checkin-circle my-4" t-on-click="openCheckInSheet">
                        Check In
                    </button>
                    <p class="checkin-subtext">Check in and start your amazing day!</p>
                </t>
            </section>

             <!-- Attendance List Card -->
             <section class="attendance-list-card mt-3">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <h5 class="fw-bold mb-0">Recent Attendance</h5>
                    <i class="fa fa-arrow-right text-muted"/>
                </div>
                
                <t t-if="state.isLoading">
                    <p class="text-center text-muted small p-3 mb-0">Loading history...</p>
                </t>
                <t t-elif="state.recentAttendance.length === 0">
                    <p class="text-center text-muted small p-3 mb-0">No attendance history found.</p>
                </t>
                <t t-else="">
                    <div class="recent-attendance-list">
                       <t t-foreach="state.recentAttendance" t-as="att" t-key="att.id">
                          <div class="recent-attendance-item">
                           
                                <div class="date-badge-sm">
                                    <span class="day" t-esc="att.day"/>
                                    <span class="month" t-esc="att.dayName"/>
                                </div>
                           

                             <div class="history-grid">
                                <div class="grid-col-sm">
                                    <div class="time-sm" t-esc="att.check_in_time"/>
                                    <div class="label-sm">Check In</div>
                                </div>
                                <div class="v-divider-sm"></div>
                                <div class="grid-col-sm">
                                    <div class="time-sm" t-esc="att.check_out_time || '--:--'"/>
                                    <div class="label-sm">Check Out</div>
                                </div>
                                <div class="v-divider-sm"></div>
                                <div class="grid-col-sm">
                                    <div class="time-sm" t-esc="att.worked_hours"/>
                                    <div class="label-sm">Total Hours</div>
                                </div>
                            </div>
                          </div>
                       </t>
                    </div>
                </t>
             </section>
          </main>
          
          <!-- === BOTTOM SHEET FOR CHECK-IN PROCESS === -->
          <div class="bottom-sheet-backdrop" 
             t-att-class="{ 'active': state.showCheckInSheet }"
             t-on-click="closeCheckInSheet"/>

          <div class="bottom-sheet" t-att-class="{ 'active': state.showCheckInSheet }">
             <div class="bottom-sheet-header">
                <div class="bottom-sheet-handle"/>
                <button class="btn-close" t-on-click="closeCheckInSheet"/>
             </div>
             <div class="bottom-sheet-content">
                <!-- Step 1: Location Selection -->
                <div t-if="state.checkInStep === 'location'">
                    <h4 class="fw-bold mb-3">Select Work Location</h4>
                    <div t-if="state.checkInError" class="alert alert-danger" t-esc="state.checkInError"/> 
                    <div t-if="state.isProcessingLocation" class="text-center p-4">
                       <div class="spinner-border text-primary" role="status"/>
                       <p class="mt-2 text-muted">Getting your location and available work sites...</p>
                    </div>                   
                    
                    <div id="checkin-map" class="checkin-map-container mb-3"/>
                    
                    <div t-if="!state.isProcessingLocation and !state.checkInError">
                       <div class="location-list">
                          <t t-if="!state.processedLocations.length">
                             <p class="text-center text-muted">No work locations found.</p>
                          </t>
                             
                          <t t-foreach="state.processedLocations" t-as="loc" t-key="loc.id">
                             <div class="location-card" 
                                t-att-class="{ 'in-range': loc.isInRange, 'out-of-range': !loc.isInRange }">
                                    
                                <div class="location-details">
                                    <h6 class="fw-bold mb-0" t-esc="loc.name"/>
                                    <span class="location-distance">
                                       <i class="fa fa-map-marker me-1"/> <t t-esc="loc.distanceString"/> away
                                    </span>
                                </div>
                                    
                                <!-- Action Button -->
                                <button t-if="loc.isInRange" 
                                    class="btn btn-primary btn-sm" 
                                    style="color:var(--app-surface);"
                                    t-on-click="() => this.selectLocationAndOpenCamera(loc)">
                                    SELECT
                                </button>
                                <span t-else="" class="range-status text-muted">
                                    Out of Range
                                </span>
                             </div>
                          </t>
                       </div>
                    </div>
                </div>

                <!-- Step 2: Camera -->
                <div t-if="state.checkInStep === 'camera'">
                     <h4 class="fw-bold mb-3">Take a Selfie</h4>
                    <!-- Show photo preview if already taken --> 
                    <div t-if="state.capturedImage" class="text-center">
                       <img t-att-src="state.capturedImage" class="camera-preview-img mb-3" alt="Captured Selfie"/>
                       <div class="camera-btn-row mt-3 justify-content-center">
                            <button class="btn btn-primary btn-lg camera-btn-submit"
                                style="color:var(--app-surface);"
                                    t-on-click="submitCheckIn"
                                    t-att-disabled="state.isSubmitting"
                            >
                                <span t-if="state.isSubmitting" class="spinner-border spinner-border-sm me-2"/>
                                Submit Check-In
                            </button>
                            <button class="btn btn-outline-secondary camera-btn-retake"
                                    t-on-click="retakePicture"
                            >
                                Retake
                            </button>
                        </div>
                    </div>

                    <!-- Show camera preview if photo not yet taken -->
                    <div t-else="" class="camera-container text-center">
                       <!-- Video element for camera stream -->
                       <video t-ref="video_preview" class="camera-preview" autoplay="1" muted="1" playsinline="1"/>
                       
                       <!-- Button to capture image -->
                       <button class="btn-capture-circle mt-3" t-on-click="takePicture">
                          <i class="fa fa-camera"/>
                       </button>
                    </div>

                    <!-- Canvas for image processing (hidden) -->
                    <canvas t-ref="canvas_capture" style="display: none;"/>
                    
                    <!-- Show camera error -->
                    <p t-if="state.checkInError" class="text-danger small mt-3 text-center" t-esc="state.checkInError"/>
                </div>
             </div>   
          </div>       
       </div>
    `;
      setup() {
        const now = new Date();
        const component = useComponent();
        this.mapInstance = null;
        this.videoRef = useRef("video_preview"); // Referensi ke elemen video
        this.canvasRef = useRef("canvas_capture"); 
        this.state = useState({
            // Nama state diubah menjadi 'timeDisplay' dan diisi dengan objek
            timeDisplay: this.formatTime(now),
            currentDate: this.formatDate(now),
            isLoading: true,
            recentAttendance: [],
            showCheckInSheet: false,
            checkInStep: 'location',
            selectedLocation: null, // <-- SIMPAN OBJEK LOKASI YANG DIPILIH
            capturedImage: null,    // <-- Simpan data URL gambar yang diambil
            isSubmitting: false,
            availableLocations: [], 
            processedLocations: [], 
            isProcessingLocation: false, // Menggantikan isFetchingLocations
            checkInError: null,
            userCoords: null,
            toast: null,
            isWorking: false,         // status sedang working
            workingSince: null,       // Date object waktu check-in terakhir aktif
            attendanceId: null,        // ID absensi terakhir (jika ada)
            activeAttendance: null,
            showCheckoutConfirm: false,
        });
        onWillStart(async () => {
            //await component.fetchAttendance(); // Memanggil method dari komponen induk jika perlu
            await Promise.all([this.fetchAttendance(), this.fetchActiveAttendance()]);
        });

        let timer;
        onMounted(() => {
            timer = setInterval(() => {
                const now = new Date();
                // State yang diupdate juga harus 'timeDisplay'
                this.state.timeDisplay = this.formatTime(now);
                if (this.state.currentDate !== this.formatDate(now)) {
                    this.state.currentDate = this.formatDate(now);
                }
                if (this.state.isWorking && this.state.workingSince) {
                    this.state.workingTimer = this.formatElapsed(now - this.state.workingSince);
                }
            }, 1000);
        });

        onWillUnmount(() => {
            clearInterval(timer);
        });
    }
    formatElapsed(ms) {
        ms = Math.max(0, ms);
        let totalSec = Math.floor(ms / 1000);
        let hours = Math.floor(totalSec / 3600);
        let minutes = Math.floor((totalSec % 3600) / 60);
        let seconds = totalSec % 60;
        return `${hours.toString().padStart(2,'0')}:${minutes.toString().padStart(2,'0')}:${seconds.toString().padStart(2, '0')}`;
    }
    showToast(type, message, timeout = 6000) { // default 6 detik
        this.state.toast = { type, message };
        setTimeout(() => {
            this.state.toast = null;
        }, timeout);
    }
    async openCheckInSheet() {
        this.state.showCheckInSheet = true;
        this.state.isProcessingLocation = true;
        this.state.checkInError = null;
        this.state.processedLocations = []; // Kosongkan data lama

        try {
            // Jalankan kedua promise (ambil lokasi GPS & fetch lokasi kerja) secara bersamaan
            const [userCoords, locationsResponse] = await Promise.all([
                this.getUserLocation(),
                fetch('/smartatt/get_work_locations', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({})
                })
            ]);
            this.state.userCoords = userCoords
            if (!locationsResponse.ok) throw new Error("Could not load work locations");
            
            const locationsData = await locationsResponse.json();
            this.state.availableLocations = locationsData.result || [];

            // Sekarang proses data: hitung jarak untuk setiap lokasi
            this.processLocationsWithDistance(userCoords);
            setTimeout(() => this.setupMap(), 0);
             
        } catch (error) {
            console.error("Error during check-in process:", error);
            this.state.checkInError = error.message || "An unknown error occurred.";
        } finally {
            this.state.isProcessingLocation = false;
        }
    }
    async selectLocationAndOpenCamera(location) {
        this.state.selectedLocation = location;
        this.state.checkInStep = 'camera';
        
        // Gunakan setTimeout untuk memastikan elemen <video> sudah ada di DOM
        // sebelum kita mencoba menggunakannya.
        setTimeout(() => this.startCamera(), 0);
    }
     async startCamera() {
        if (!this.videoRef.el) {
            this.state.checkInError = "Camera element not found.";
            return;
        }

        try {
            const stream = await navigator.mediaDevices.getUserMedia({ 
                video: { facingMode: 'user' }, // Prioritaskan kamera depan
                audio: false 
            });
            this.videoRef.el.srcObject = stream;
        } catch (err) {
            console.error("Camera Error:", err);
            this.state.checkInError = "Could not access camera. Please grant permission.";
            // Jika gagal, kembali ke langkah pemilihan lokasi
            this.state.checkInStep = 'location';
        }
    }

    // Mengambil gambar dari video
    takePicture() {
        if (!this.videoRef.el || !this.canvasRef.el) return;

        const video = this.videoRef.el;
        const canvas = this.canvasRef.el;
        const context = canvas.getContext('2d');

        // Sesuaikan ukuran canvas dengan ukuran video
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        
        // Gambar frame video saat ini ke canvas
        context.drawImage(video, 0, 0, video.videoWidth, video.videoHeight);

        // Simpan gambar sebagai data URL (format JPEG kualitas 0.8)
        const dataUrl = canvas.toDataURL('image/jpeg', 0.8);
        this.state.capturedImage = dataUrl;

        // Hentikan stream kamera setelah foto diambil untuk menghemat baterai
        const stream = video.srcObject;
        const tracks = stream.getTracks();
        tracks.forEach(track => track.stop());
        video.srcObject = null;
    }

    // Kembali ke pratinjau kamera dari tampilan foto
    retakePicture() {
        this.state.capturedImage = null;
        this.state.checkInError = null;
        // Restart kamera
        setTimeout(() => this.startCamera(), 0);
    }
    // ... (di dalam kelas Dashboard)

    async submitCheckIn() {
        this.state.isSubmitting = true;
        this.state.checkInError = null;

        try {
            // --- Persiapkan data untuk dikirim ---
            const payload = {
                location_id: this.state.selectedLocation.id,
                image_data: this.state.capturedImage, // Ini adalah data URL Base64
                user_latitude: this.state.userCoords.latitude,
                user_longitude: this.state.userCoords.longitude,
            };
            console.log("Check-in payload:", payload);

            // --- Kirim data ke server Odoo ---
            const response = await fetch('/smartatt/submit_check_in', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const result = await response.json();
            console.log("Check-in response:", result);
            // Cek jika ada error dari server (misal, BadRequest, NotFound)
            if (!response.ok) {
                // Error yang dikirim oleh werkzeug.exceptions biasanya ada di result.error
                throw new Error(result.error.message || 'An error occurred on the server.');
            }

            // --- Handle Sukses ---
            // Anda bisa menampilkan notifikasi yang lebih canggih di sini
        // alert(result.result.message || 'Check-in successful!');
        console.log("Response status:", result.result.status);
        
            if (result.result.status === 'success') {
                this.showToast('success', result.result.message || 'Check-in successful!');
            } else {
                this.showToast('error', result.result.message || 'Check-in failed!');
            }
            
            // Tutup dan reset bottom sheet
            this.closeCheckInSheet();

            // PENTING: Refresh daftar riwayat absensi di dashboard
            await this.fetchAttendance();
            await this.fetchActiveAttendance();

        } catch (error) {
            console.error("Failed to submit check-in:", error);
            this.state.checkInError = `Submission failed: ${error.message}`;
        } finally {
            this.state.isSubmitting = false;
        }
    }
    async doCheckoutNow() {
        // Dapatkan lokasi GPS terbaru sebelum kirim, bisa juga gunakan lokasi checkin sebelumnya (userCoords), di sini pakai getUserLocation()
        this.state.isSubmitting = true;
        try {
            // Dapatkan GPS terkini
            const coords = await this.getUserLocation();
            const payload = {
                attendance_id: this.state.attendanceId,
                out_latitude: coords.latitude,
                out_longitude: coords.longitude,
            };
            console.log("Checkout payload:", payload);
            const response = await fetch('/smartatt/submit_check_out', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const result = await response.json();
            console.log("Checkout response:", result);
            if (!response.ok || !result.result || result.result.status !== 'success') {
                const msg = (result.result && result.result.message) || result.message || "Checkout gagal";
                throw new Error(msg);
            }
            this.showToast('success', result.result.message || "Checkout berhasil!");
            this.state.showCheckoutConfirm = false;
            await this.fetchAttendance();
            await this.fetchActiveAttendance();
        } catch (err) {
            this.showToast('error', (err && err.message) || "Checkout gagal");
        } finally {
            this.state.isSubmitting = false;
        }
    }
    // 1. Helper untuk mendapatkan lokasi GPS pengguna (menggunakan Promise)
    getUserLocation() {
        return new Promise((resolve, reject) => {
            if (!("geolocation" in navigator)) {
                reject(new Error("Geolocation is not supported by your browser."));
                return;
            }
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    resolve({
                        latitude: position.coords.latitude,
                        longitude: position.coords.longitude,
                    });
                },
                (error) => {
                    // Handle berbagai macam error GPS
                    switch(error.code) {
                        case error.PERMISSION_DENIED:
                            reject(new Error("Location access was denied. Please enable it in your browser settings."));
                            break;
                        case error.POSITION_UNAVAILABLE:
                            reject(new Error("Location information is unavailable."));
                            break;
                        case error.TIMEOUT:
                            reject(new Error("The request to get user location timed out."));
                            break;
                        default:
                            reject(new Error("An unknown error occurred while getting location."));
                            break;
                    }
                },
                { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 } // Opsi untuk akurasi tinggi
            );
        });
    }

    // 2. Helper untuk menghitung jarak (Haversine formula)
    calculateDistance(lat1, lon1, lat2, lon2) {
        const R = 6371e3; // Radius bumi dalam meter
        const φ1 = lat1 * Math.PI / 180;
        const φ2 = lat2 * Math.PI / 180;
        const Δφ = (lat2 - lat1) * Math.PI / 180;
        const Δλ = (lon2 - lon1) * Math.PI / 180;

        const a = Math.sin(Δφ / 2) * Math.sin(Δφ / 2) +
                  Math.cos(φ1) * Math.cos(φ2) *
                  Math.sin(Δλ / 2) * Math.sin(Δλ / 2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

        return R * c; // Hasil dalam meter
    }
    
    // 3. Helper untuk memproses dan menambahkan info jarak ke setiap lokasi
    processLocationsWithDistance(userCoords) {
        this.state.processedLocations = this.state.availableLocations.map(loc => {
            const distance = this.calculateDistance(
                userCoords.latitude, userCoords.longitude,
                loc.latitude, loc.longitude
            );
 
            const isInRange = distance <= loc.radius;
 
            
            // Format jarak agar lebih mudah dibaca
            let distanceString = distance > 1000 
                ? `${(distance / 1000).toFixed(2)} km`
                : `${Math.round(distance)} m`;

            return {
                ...loc,
                distance: distance,
                distanceString: distanceString,
                isInRange: isInRange,
            };
        });
    }
    closeCheckInSheet() {
         // 1. Sembunyikan sheet
        this.state.showCheckInSheet = false;

        // 2. Hancurkan instance peta untuk membebaskan memori
        if (this.mapInstance) {
            this.mapInstance.remove();
            this.mapInstance = null;
        }

        // 3. Hentikan stream kamera jika masih berjalan (penting!)
        if (this.videoRef.el && this.videoRef.el.srcObject) {
            const stream = this.videoRef.el.srcObject;
            const tracks = stream.getTracks();
            tracks.forEach(track => track.stop());
            this.videoRef.el.srcObject = null;
        }

        // 4. Reset semua state yang berhubungan dengan proses check-in
        this.state.checkInStep = 'location';      // <-- KEMBALIKAN KE LANGKAH AWAL
        this.state.selectedLocation = null;
        this.state.capturedImage = null;
        this.state.checkInError = null;
        this.state.isSubmitting = false;
        this.state.processedLocations = [];
        this.state.userCoords = null;
    }
    setupMap() {
        if (!this.state.userCoords || this.mapInstance) {
            return;
        }
        
        // Inisialisasi peta pada elemen dengan id="checkin-map"
        this.mapInstance = L.map('checkin-map').setView([this.state.userCoords.latitude, this.state.userCoords.longitude], 15);
        this.mapInstance.invalidateSize();
        // Tambahkan layer tile (misal dari OpenStreetMap)
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(this.mapInstance);

        // Tambahkan marker untuk posisi pengguna
        const userLocationIcon = L.AwesomeMarkers.icon({
            icon: 'user',        // Ikon dari Font Awesome
            prefix: 'fa',        // Prefix untuk Font Awesome
            markerColor: 'red',  // Warna marker: 'red', 'blue', 'green', 'purple', 'orange', 'cadetblue'
            iconColor: 'white'   // Warna ikon di dalamnya
        });
        L.marker([this.state.userCoords.latitude, this.state.userCoords.longitude], {
        icon: userLocationIcon
    }).addTo(this.mapInstance).bindPopup("Your Location");
       

        // Tambahkan marker dan lingkaran radius untuk setiap lokasi kerja
        this.state.processedLocations.forEach(loc => {
            // Marker untuk titik pusat lokasi
            L.marker([loc.latitude, loc.longitude]).addTo(this.mapInstance)
                .bindPopup(`<b>${loc.name}</b>`);

            // Lingkaran untuk radius
            L.circle([loc.latitude, loc.longitude], {
                color: loc.isInRange ? 'green' : 'red',
                fillColor: loc.isInRange ? '#90ee90' : '#f08080',
                fillOpacity: 0.3,
                radius: loc.radius // radius dalam meter
            }).addTo(this.mapInstance);
        });
    }
    async fetchActiveAttendance() {
        try {
            const response = await fetch('/smartatt/get_attendance_history', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ params: { limit: 1 } }) // Ambil hanya 1 terbaru
            });
            if (!response.ok) throw new Error("Failed to fetch attendance");

            const data = await response.json();
            const rawHistory = Array.isArray(data.result) ? data.result : [];
            // Cari entry yg check_in AADA & check_out NULL (masih kerja)
            if (rawHistory.length && rawHistory[0].check_in && !rawHistory[0].check_out) {
                const att = rawHistory[0];
                const checkInDate = new Date(att.check_in);
                this.state.isWorking = true;
                this.state.workingSince = checkInDate;
                this.state.attendanceId = att.id;
                // Simpan info lain untuk card utama jika mau (misal lokasi kerja)
                this.state.activeAttendance = {
                    id: att.id,
                    workingSince: checkInDate,
                    location: att.work_location_name || '-',
                    // dst
                };
            } else {
                this.state.isWorking = false;
                this.state.workingSince = null;
                this.state.attendanceId = null;
                this.state.activeAttendance = null;
            }
        } catch (error) {
            this.state.isWorking = false;
            this.state.workingSince = null;
            this.state.attendanceId = null;
            this.state.activeAttendance = null;
        }
    }
    async fetchAttendance() {

        this.state.isLoading = true;
        try {        
            const response = await fetch('/smartatt/get_attendance_history', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ params: { limit: 5 } })
            });           
            if (!response.ok) { 
                throw new Error("Failed to fetch attendance, status: " + response.status); 
            }
            const data = await response.json();
            const rawHistory = Array.isArray(data.result) ? data.result : [];
            const processedHistory = rawHistory.map(att => {
                // Buat objek Date dari string ISO yang dikirim backend
                const checkInDate = new Date(att.check_in);
                const checkOutDate = att.check_out ? new Date(att.check_out) : null;

                // Kembalikan objek BARU dengan format yang diinginkan template
                return {
                    id: att.id,
                    day: checkInDate.getDate(),
                    dayName: checkInDate.toLocaleString('en-US', { weekday: 'short' }),
                    check_in_time: checkInDate.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', hour12: false }),
                    check_out_time: checkOutDate ? checkOutDate.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', hour12: false }) : null,
                   // worked_hours: att.worked_hours,
                    worked_hours: workedHoursStr(att.worked_hours),
                };
            });
            
            // Masukkan data yang sudah diolah ke dalam state
            this.state.recentAttendance = processedHistory;
         

        } catch (error) {
            console.error("Error fetching attendance history:", error);
            this.state.recentAttendance = [];
        } finally {
            this.state.isLoading = false;
          
        }
    }

    // Helper function untuk format waktu (HH:MM:SS)
     formatTime(date) {
        let hours = date.getHours();
        const minutes = String(date.getMinutes()).padStart(2, '0');
        const ampm = hours >= 12 ? 'PM' : 'AM';
        hours = hours % 12;
        hours = hours ? hours : 12; // Jam 0 harus menjadi 12
        
        return {
            time: `${String(hours).padStart(2, '0')}:${minutes}`, // Hanya jam dan menit
            ampm: ampm
        };
    }
    formatDate(date) {
        const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
        return date.toLocaleDateString('en-US', options);
    }
}