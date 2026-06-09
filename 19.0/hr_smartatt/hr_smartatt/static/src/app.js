/** @odoo-module **/
import { Component, useState, xml, whenReady, mount, onMounted, onWillUnmount } from "@odoo/owl";
import { templates } from "@web/core/assets";

import { LoginForm } from "./components/LoginForm";
import { Dashboard } from "./components/Dashboard";
import { Account } from "./components/Account";
import { BottomBar } from "./components/BottomBar";
import { AttendanceHistory } from "./components/AttendanceHistory";

class MainApp extends Component {
    static components = { LoginForm, Dashboard, Account, BottomBar, AttendanceHistory }; 
    static template = xml`
        <div class="mobile-frame">
            <t t-if="!state.isLoggedIn">
                <LoginForm onLoginSuccess.bind="onLoginSuccess" />
            </t>
            <t t-else="">
                <!-- PENYESUAIAN 4: Struktur Baru untuk Sticky Bottom Bar -->

                <!-- Area Konten yang Bisa Di-scroll -->
                <div class="content-scrollable">
                    <t t-if="state.route.page === 'dashboard'">
                        <Dashboard employee="state.employee" onNavigate.bind="navigate"/>
                    </t>
                    <t t-if="state.route.page === 'account'">
                        <Account employee="state.employee" onLogout.bind="onLogout" />
                    </t>
                    <t t-if="state.route.page === 'history'">
                        <AttendanceHistory />
                    </t>
                </div>

                <!-- Bottom Bar sekarang berada di luar area scroll -->
                <BottomBar 
                    currentPage="state.route.page" 
                    onNavigate.bind="navigate" 
                />
            </t>
        </div>
    `;

    setup() {
        const root = document.getElementById("smartatt_app_root");
        if (!root) {
            console.error("Target mounting 'smartatt_app_root' tidak ditemukan.");
            return;
        }

        this.state = useState({
            isLoggedIn: root.dataset.isLoggedIn === "True",
            employee: {
                name: root.dataset.userName || 'Karyawan',
                id: parseInt(root.dataset.employeeId, 10) || 0,
                department: root.dataset.employeeDepartment || 'N/A',
                jobTitle: root.dataset.employeeJobTitle || 'N/A',
                avatarUrl: root.dataset.employeeAvatarUrl || ''
            },
            route: this.parseHash(window.location.hash)
        });

        this.handleHashChange = () => { this.state.route = this.parseHash(window.location.hash); };
        onMounted(() => window.addEventListener('hashchange', this.handleHashChange));
        onWillUnmount(() => window.removeEventListener('hashchange', this.handleHashChange));
    }

    parseHash(hash) {
        const page = hash.substring(1) || 'dashboard'; // Disederhanakan untuk 'dashboard' atau 'account'
        return { page };
    }
    
    navigate(page) {
        window.location.hash = page;
    }
    
    async onLoginSuccess() {
        try {
            // Gunakan fetch standar untuk memanggil endpoint JSON kita.
            // Cookie sesi akan otomatis ditangani oleh browser.
            console.log("Memanggil endpoint untuk mengambil data karyawan...");
            const response = await fetch('/smartatt/get_employee_data', {
                method: 'POST', // type='json' di Odoo biasanya menggunakan POST
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({}) // Kirim body JSON kosong
                
            });
            console.log("Response dari server:", response);

            if (!response.ok) {
                // Jika server mengembalikan error (misal 404, 500)
                console.error("Gagal mengambil data employee, status:", response.status);
                // Fallback: reload halaman, ini aman
                window.location.replace("/smartatt#dashboard");
                return;
            }

            const result = await response.json();
            console.log("Data JSON diterima:", result);
            const employeeData = result.result; // Data dari controller JSON ada di dalam 'result'
            console.log("Data karyawan:", employeeData);

            if (employeeData) {
                // Perbarui state secara langsung, tidak perlu reload halaman
                this.state.employee.id = employeeData.id;
                this.state.employee.name = employeeData.name;
                this.state.employee.department = employeeData.department;
                this.state.employee.jobTitle = employeeData.job_title;
                this.state.employee.avatarUrl = employeeData.avatar_url;
                this.state.isLoggedIn = true;
                this.state.route.page = 'dashboard';
                // Perbarui hash di URL secara manual
                window.history.pushState(null, '', '#dashboard');
            } else {
                // Jika data employee tidak ditemukan (misal, bukan karyawan)
                // Lakukan logout paksa
                window.location.href = '/web/session/logout?redirect=/smartatt';
            }
        } catch (error) {
            console.error("Terjadi kesalahan pada saat login:", error);
            // Fallback jika ada error jaringan atau parsing
            window.location.replace("/smartatt#dashboard");
        }
    }
    onLogout() { window.location.href = '/web/session/logout?redirect=/smartatt'; }
}

// Mount aplikasi
whenReady(() => {
    const root = document.getElementById("smartatt_app_root");
    if (root) {
        if (root.dataset.isLoggedIn !== undefined) {
             mount(MainApp, root, { templates, dev: true });
        }
    }
});