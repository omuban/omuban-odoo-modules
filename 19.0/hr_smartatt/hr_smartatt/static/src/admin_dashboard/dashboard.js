/** @odoo-module */

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, useState, onMounted, useRef,onWillUnmount } from "@odoo/owl";

function loadChartJsFromCDN() {
    return new Promise((resolve, reject) => {
        if (window.Chart) {
            return resolve(); // Sudah ada, lanjut
        }
        const script = document.createElement("script");
        script.src = "https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js";
        script.async = true;
        script.onload = () => resolve();
        script.onerror = () => reject(new Error("Gagal load Chart.js"));
        document.head.appendChild(script);
    });
}

export class SmartAttendanceDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.lineChartRef = useRef("lineChart");       
        this.locationChartRef = useRef("locationChart"); // <--- Ref Baru
        
        this.state = useState({
            stats: {
                total_employees: 0,
                total_locations: 0,
                present_count: 0,
                absent_count: 0
            }
        });

        onWillStart(async () => {
            await Promise.all([
                loadChartJsFromCDN(),
                this.loadData(),
                this.loadChartData()
            ]);
        });
        onMounted(() => {
            this.renderLineChart();
            this.renderLocationChart(); // <--- Render chart kedua
        });
        onWillUnmount(() => {
            // Bersihkan kedua chart
            if (this.lineChartInstance) this.lineChartInstance.destroy();
            if (this.locationChartInstance) this.locationChartInstance.destroy();
        });
    }

    async loadData() {
        // Panggil method Python 'get_dashboard_data'
        const result = await this.orm.call("hr.attendance", "get_dashboard_data", []);
        this.state.stats = result;
    }
    async loadChartData() {
        this.chartData = await this.orm.call("hr.attendance", "get_chart_data", []);
    }
    renderLineChart() {
        if (!this.lineChartRef.el || !window.Chart) return;
        if (this.lineChartInstance) this.lineChartInstance.destroy();

        // Ambil data counts dari state yang dikirim Python
        const weeklyCounts = this.chartData.weekly_counts; 

        const config = {
            type: 'line',
            data: {
                labels: this.chartData.weekly_labels,
                datasets: [{
                    label: 'Attendance Rate',
                    data: this.chartData.weekly_data, // Y-Axis tetap Persentase
                    borderColor: '#0d6efd',
                    backgroundColor: 'rgba(13, 110, 253, 0.1)',
                    borderWidth: 3,
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { 
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            // Kustomisasi Label Tooltip
                            label: function(context) {
                                // context.raw = nilai persentase (sumbu Y)
                                // context.dataIndex = urutan hari (0-6)
                                
                                const percentage = context.raw;
                                const count = weeklyCounts[context.dataIndex]; // Ambil jumlah orang
                                
                                // Format Output: "85.5% (42 Employees)"
                                return `${percentage}% (${count} Employees)`;
                            }
                        }
                    }
                },
                scales: {
                    y: { 
                        beginAtZero: true, 
                        max: 100,
                        ticks: { callback: (val) => val + "%" },
                        grid: { borderDash: [2, 4] }
                    },
                    x: { grid: { display: false } }
                }
            }
        };
        this.lineChartInstance = new window.Chart(this.lineChartRef.el, config);
    }
    renderLocationChart() {
        if (!this.locationChartRef.el || !window.Chart) return;
        if (this.locationChartInstance) this.locationChartInstance.destroy();

        // Cek jika data kosong
        if (this.chartData.location_data.length === 0) {
            // Bisa handle tampilan "No Data" jika mau
            return; 
        }

        const config = {
            type: 'doughnut',
            data: {
                labels: this.chartData.location_labels,
                datasets: [{
                    data: this.chartData.location_data,
                    backgroundColor: [
                        '#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b', 
                        '#858796', '#5a5c69', '#fd7e14', '#20c997', '#6f42c1'
                    ], // Palette warna
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { boxWidth: 12, font: { size: 10 } }
                    },
                    title: {
                        display: false,
                        text: 'Work Locations Distribution'
                    }
                },
                cutout: '70%', // Membuat lubang donat lebih besar
            }
        };
        this.locationChartInstance = new window.Chart(this.locationChartRef.el, config);
    }

    // Fungsi navigasi saat kartu diklik
     openView(viewName) {
        let domain = [];
        let res_model = 'hr.employee';
        let name = 'Employees';

        // Logika Navigasi
        if (viewName === 'employees') {
            res_model = 'hr.employee';
            name = 'All Employees';
        } else if (viewName === 'locations') { // <--- Case Baru
            res_model = 'hr.work.location';
            name = 'Work Locations';
        } else if (viewName === 'present') {
            res_model = 'hr.attendance';
            name = 'Present Today';
            const today = new Date().toISOString().split('T')[0];
            domain = [['check_in', '>=', today + ' 00:00:00']];
        } else if (viewName === 'absent') {
             // Logic absent bisa kompleks, biasanya buka list employee filter absent
             // Disini kita buka list employee saja sebagai contoh
             res_model = 'hr.employee';
             name = 'Employees';
        }

        this.action.doAction({
            type: 'ir.actions.act_window',
            name: name,
            res_model: res_model,
            views: [[false, 'list'], [false, 'form']],
            domain: domain,
        });
    }
}

SmartAttendanceDashboard.template = "hr_smartatt.DashboardTemplate";

// Tag ini harus sama dengan field 'tag' di XML action
registry.category("actions").add("hr_smartatt_admin_dashboard", SmartAttendanceDashboard);