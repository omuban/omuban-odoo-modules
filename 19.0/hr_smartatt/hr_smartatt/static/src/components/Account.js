/** @odoo-module **/
import { Component, xml } from "@odoo/owl";

export class Account extends Component {
    static props = {
        employee: { type: Object },
        onLogout: { type: Function },
    };
    
    // --- TEMPLATE BARU DENGAN DESAIN TEMA ---
    static template = xml`
        <div class="account-page">
            <!-- 1. Profile Header -->
            <header class="account-header text-center text-white">
                <img t-att-src="props.employee.avatarUrl" class="profile-avatar mb-3" alt="Avatar"/>
                <h4 class="fw-bold mb-0" t-esc="props.employee.name"/>
                <p class="opacity-75 mb-0" t-esc="props.employee.jobTitle"/>
            </header>

            <!-- 2. Konten & Daftar Informasi -->
            <main class="account-content p-3">
                <div class="info-card">
                    <!-- Item Department -->
                    <div class="info-item">
                        <div class="info-icon-wrapper bg-secondary-soft text-secondary">
                            <i class="fa fa-building"/>
                        </div>
                        <div class="flex-grow-1">
                            <span class="info-label">Department</span>
                            <p class="info-value" t-esc="props.employee.department"/>
                        </div>
                        <i class="fa fa-chevron-right text-muted"/>
                    </div>

                    <!-- Item Employee ID -->
                    <div class="info-item">
                        <div class="info-icon-wrapper bg-secondary-soft text-secondary">
                            <i class="fa fa-id-card-o"/>
                        </div>
                        <div class="flex-grow-1">
                            <span class="info-label">Employee ID</span>
                            <p class="info-value" t-esc="props.employee.id"/>
                        </div>
                        <i class="fa fa-chevron-right text-muted"/>
                    </div>
                </div>

                <!-- 3. Tombol Logout -->
                <div class="logout-card mt-3" t-on-click="props.onLogout">
                    <div class="info-item">
                        <div class="info-icon-wrapper bg-danger-soft text-danger">
                            <i class="fa fa-sign-out"/>
                        </div>
                        <div class="flex-grow-1">
                            <p class="info-value text-danger">Logout</p>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    `;
}