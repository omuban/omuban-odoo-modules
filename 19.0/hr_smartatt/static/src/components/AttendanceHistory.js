/** @odoo-module **/
import { Component, xml, onWillStart, useState } from "@odoo/owl";
function workedHoursStr(hours) {
    if (typeof hours !== 'number' || isNaN(hours)) return '00:00';
    const h = Math.floor(hours);
    const m = Math.round((hours - h) * 60);
    return `${h.toString().padStart(2,'0')}:${m.toString().padStart(2,'0')}`;
}
export class AttendanceHistory extends Component {
     static template = xml`
        <div class="history-page p-3">
            <header class="mb-3">
                <h3 class="fw-bold">Attendance History</h3>
            </header>

            <!-- KARTU PEMBUNGKUS BARU -->
            <div class="history-card">
                <t t-if="state.isLoading">
                    <div class="text-center p-5">
                        <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden">Loading...</span>
                        </div>
                    </div>
                </t>
                <t t-elif="!state.attendance.length">
                    <p class="text-center text-muted p-4 mb-0">No attendance history found.</p>
                </t>
                <t t-else="">
                    <!-- Hapus 'list-group-flush' agar tidak ada style yang bentrok -->
                    <ul class="list-group">
                        <t t-foreach="state.attendance" t-as="att" t-key="att.id">
                            <li class="list-group-item attendance-record2">
                                <div class="date-badge2">
                                    <span class="day" t-esc="att.day"/>
                                    <span class="month" t-esc="att.dayName"/>
                                </div>
                                <div style="flex:1; display:flex; flex-direction:column;">
                                    <div class="history-grid">
                                        <div class="grid-col">
                                            <div class="time-lg" t-esc="att.check_in_time"/>
                                            <div class="label">Check In</div>
                                        </div>
                                        <div class="v-divider"></div>
                                        <div class="grid-col">
                                            <div class="time-lg" t-esc="att.check_out_time || '--:--'"/>
                                            <div class="label">Check out</div>
                                        </div>
                                        <div class="v-divider"></div>
                                        <div class="grid-col">
                                            <div class="time-lg" t-esc="att.worked_hours_str"/>
                                            <div class="label">Total Hours</div>
                                        </div>
                                    </div>
                                    <div class="location-row">
                                        <i class="fa fa-map-marker me-1 text-muted"/>
                                        <span t-esc="att.work_location_name"/>
                                    </div>
                                </div>
                            </li>
                        </t>
                    </ul>
                </t>
            </div>
        </div>
    `;

    setup() {
        this.state = useState({
            attendance: [],
            isLoading: true,
        });

        onWillStart(async () => {
            await this.loadHistory();
        });
    }
     

    async loadHistory() {
        const response = await fetch('/smartatt/get_attendance_history', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({}),
        });
        const result = await response.json();
        const rawHistory = result.result || [];

        // Proses data mentah menjadi format yang lebih mudah ditampilkan
        this.state.attendance = rawHistory.map(att => {
            // Cek jika check_in ada sebelum membuat objek Date
            const checkInDate = att.check_in ? new Date(att.check_in) : null;
            const checkOutDate = att.check_out ? new Date(att.check_out) : null;
            
            return {
                // <-- Ini sudah berisi 'id', 'worked_hours', dan 'work_location_name'
                ...att,
                day: checkInDate ? checkInDate.getDate() : '?',
                month: checkInDate ? checkInDate.toLocaleString('en-US', { month: 'short' }) : '???',
                dayName: checkInDate ? checkInDate.toLocaleString('en-US', { weekday: 'short' }) : '???',
                check_in_time: checkInDate ? checkInDate.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', hour12: false }) : '--:--',
                check_out_time: checkOutDate ? checkOutDate.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', hour12: false }) : null,
                worked_hours_str: workedHoursStr(att.worked_hours),
                // work_location_name sudah ada dari '...att'
            };
        });
        this.state.isLoading = false;
    }
    
}