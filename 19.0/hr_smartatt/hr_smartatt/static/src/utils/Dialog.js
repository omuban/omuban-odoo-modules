/** @odoo-module **/
import { Component, xml } from "@odoo/owl";

export class Dialog extends Component {
    static template = xml`
        <!-- Latar belakang gelap semi-transparan -->
        <div t-if="props.isActive" class="dialog-backdrop d-flex justify-content-center align-items-center" t-on-click.self="props.onCancel">
            <!-- Kotak Dialog -->
            <div class="dialog-box card shadow-lg" role="dialog" aria-modal="true" t-att-aria-labelledby="dialogTitle">
                <!-- Header -->
                <div class="card-header d-flex justify-content-between align-items-center">
                    <h5 class="modal-title mb-0" id="dialogTitle"><t t-esc="props.title"/></h5>
                    <button type="button" class="btn-close" aria-label="Close" t-on-click="props.onCancel"></button>
                </div>
                <!-- Body -->
                <div class="card-body">
                    <!-- 't-slot' memungkinkan kita memasukkan konten dari parent -->
                    <t t-slot="default">
                        <p>Apakah Anda yakin?</p>
                    </t>
                </div>
                <!-- Footer dengan tombol aksi -->
                <div class="card-footer text-end">
                    <button type="button" class="btn btn-secondary me-2" t-on-click="props.onCancel">
                        <t t-esc="props.cancelText"/>
                    </button>
                    <button type="button" class="btn btn-danger" t-on-click="props.onConfirm">
                        <t t-esc="props.confirmText"/>
                    </button>
                </div>
            </div>
        </div>
    `;

    // Tentukan props yang diterima oleh komponen ini
    static props = {
        isActive: { type: Boolean, optional: true },
        title: { type: String },
        onConfirm: { type: Function },
        onCancel: { type: Function },
        confirmText: { type: String, optional: true },
        cancelText: { type: String, optional: true },
        slots: { type: Object, optional: true }, // Untuk menerima konten body
    };

    // Nilai default untuk props yang opsional
    static defaultProps = {
        isActive: false,
        confirmText: "Konfirmasi",
        cancelText: "Batal",
    };
}