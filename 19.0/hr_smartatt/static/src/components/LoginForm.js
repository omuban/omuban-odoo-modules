/** @odoo-module **/
import { Component, useState, xml } from "@odoo/owl";

export class LoginForm extends Component {
    static props = ["onLoginSuccess"]; 
    setup() {
        const root = document.getElementById("smartatt_app_root");
        this.state = useState({
            login: "",
            password: "",
            error: root.dataset.errorMessage || "",
            loading: false, // Tambahkan state loading
            currentYear: new Date().getFullYear()
        });
    }

    async _onSubmit() {
        if (!this.state.login || !this.state.password) {
            this.state.error = "Email dan password wajib diisi.";
            return;
        }

        this.state.loading = true;
        this.state.error = "";

        try {
            const params = new URLSearchParams();
            params.append('login', this.state.login);
            params.append('password', this.state.password);
            
            if (window.odoo && odoo.csrf_token) {
                params.append('csrf_token', odoo.csrf_token);
            }
            
            params.append('type', 'password');

            const response = await fetch("/web/login", {
                method: "POST",
                body: params,
                headers: { "Content-Type": "application/x-www-form-urlencoded" },
                redirect: "manual"
            });
            console.log("Login response:", response);
           if (response.ok || response.type === 'opaqueredirect') {
                // Jika login berhasil, panggil onLoginSuccess.
                console.log("Login berhasil");
                this.props.onLoginSuccess();
            } else {
                const errorData = await response.json().catch(() => null);
                this.state.error = errorData?.data?.message || "Login gagal. Periksa kembali email dan password Anda.";
                this.state.loading = false;
            }
        } catch (e) {
            this.state.error = "Terjadi kesalahan koneksi ke server.";
            this.state.loading = false;
        }
    }
    togglePassword() {
        this.state.showPassword = !this.state.showPassword;
    }

    static template = xml`
        <div class="login-container">
            <div class="login-content p-4">
                <div class="login-card">
                    <!-- LOGO -->
                    <div class="login-logo-wrapper mb-4 text-center">
                        <img src="/hr_smartatt/static/src/img/logo.png" alt="Logo" class="login-logo"/>
                    </div>
                    <!-- Header -->
                    <div class="mb-4">
                        <h1 class="fw-bold-login">Login</h1>
                        <p class="text-muted welcome-login">Welcome to Smart Attendance App.</p>
                    </div>
                    <!-- Error Message -->
                    <t t-if="state.error">
                        <div class="alert alert-danger small py-2 mb-3" role="alert">
                            <t t-esc="state.error"/>
                        </div>
                    </t>
                    <!-- Form -->
                    <form t-on-submit.prevent="_onSubmit">
                        <div class="mb-3">
                            <label for="login-email" class="form-label small text-muted">Username/ Employee ID</label>
                            <input id="login-email" type="text" class="form-control form-control-lg login-input" placeholder="Enter your username" t-model="state.login" required="1"/>
                        </div>
                        <div class="mb-3">
                            <label for="login-password" class="form-label small text-muted">Password</label>
                            <div class="password-wrapper">
                                <input id="login-password" 
                                    t-att-type="state.showPassword ? 'text' : 'password'" 
                                    class="form-control form-control-lg login-input" 
                                    placeholder="Enter your password" 
                                    t-model="state.password" required="1"/>
                                <button type="button" class="btn-show-password" t-on-click="togglePassword">
                                    <i t-att-class="state.showPassword ? 'fa fa-eye-slash' : 'fa fa-eye'"/>
                                </button>
                            </div>
                        </div>
                        <div class="mb-3"> 
                            <button class="btn-login" 
                                    t-on-click="_onSubmit" 
                                    t-att-disabled="state.loading">
                                <t t-if="state.loading">
                                    <span class="spinner-border spinner-border-sm me-2"/>
                                </t>
                                Login
                            </button>
                        </div>
                    </form>
                </div>
            </div>
            <!-- Footer dengan Tombol Login -->
            <div class="bottom-bar">
                <label class="small text-muted">
                     Copyright © 2026 <a href="https://selstudio.id" style="font-weight: 600;">Sel Studio</a>. All rights reserved.
                </label>
            </div>
        </div>
    `;
}