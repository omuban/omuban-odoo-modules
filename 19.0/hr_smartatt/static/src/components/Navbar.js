/** @odoo-module **/
import { Component, xml, useState } from "@odoo/owl";

export class Navbar extends Component {
   // static props = ["state.employee.name", "onLogout", "onNavigate", "currentPage"];
    static props = {
        userName: { type: String },
        onLogout: { type: Function },
        onNavigate: { type: Function },
        currentPage: { type: String },
    };
    static template = xml`
        <nav class="navbar navbar-expand-lg navbar-dark bg-primary shadow-sm px-3">
            <a class="navbar-brand fw-bold" href="#" t-on-click.prevent="() => this.navigate('dashboard')">
                <i class="fa fa-bolt me-2"></i>Smart Attendance
            </a>
            
            <!-- Tombol Hamburger untuk Mobile -->
            <button class="navbar-toggler" type="button" t-on-click="() => this.state.isMenuOpen = !this.state.isMenuOpen">
                <span class="navbar-toggler-icon"></span>
            </button>

            <!-- Konten Navbar yang bisa disembunyikan -->
            <div class="collapse navbar-collapse" t-att-class="{ 'show': state.isMenuOpen }">
                
                <!-- Menu Navigasi -->
                <div class="navbar-nav me-auto mt-2 mt-lg-0">
                      
                </div>

                <!-- Info User (dipisah untuk layout mobile) -->
                <div class="navbar-nav ms-lg-auto mt-3 mt-lg-0">
                    <div class="d-flex align-items-center text-white">
                        <!-- Sembunyikan teks "Halo" di layar kecil (xs) untuk menghemat ruang -->
                        <span class="d-none d-sm-inline me-3">
                            Halo, <b t-esc="props.userName" />
                        </span>
                        <button class="btn btn-danger w-100 w-sm-auto" t-on-click="props.onLogout">
                            <i class="fa fa-sign-out me-1"></i> Logout
                        </button>
                    </div>
                </div>
            </div>
        </nav>
    `;

    setup() {
        this.state = useState({
            isMenuOpen: false
        });
    }

    navigate(page) {
        // Panggil props dari parent
        this.props.onNavigate(page);
        // Otomatis tutup menu setelah navigasi di mobile
        this.state.isMenuOpen = false;
    }
}