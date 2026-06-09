/** @odoo-module **/

import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component, onMounted, onWillUnmount, useRef, useEffect } from "@odoo/owl";

export class LocationPicker extends Component {
    static template = "hr_smartatt.LocationPickerField";
    static props = { ...standardFieldProps };

    setup() {
        super.setup();
        this.mapContainer = useRef("mapContainer");
        this.map = null;
        this.marker = null;
        this.circle = null; 

       // onMounted(() => this.initializeMap());
         useEffect(
            () => this.renderOrUpdateMap(),
            // Tambahkan radius ke daftar dependensi
            () => [this.props.record.data.latitude, this.props.record.data.longitude, this.props.record.data.radius]
        );
        onWillUnmount(() => {
            if (this.map) {
                this.map.remove();
                this.map = null;
            }
        });
    }
    renderOrUpdateMap() {
        // Ambil koordinat terbaru dari props
        const hasCoords = this.props.record.data.latitude && this.props.record.data.longitude;
        const lat = hasCoords ? this.props.record.data.latitude : -6.2088;
        const lng = hasCoords ? this.props.record.data.longitude : 106.8456;
        const radius = this.props.record.data.radius || 50;
        const zoom = hasCoords ? 15 : 7;

        // Cek jika peta belum dibuat sama sekali
        if (!this.map) {
            // Inisialisasi Peta untuk pertama kali
            this.map = L.map(this.mapContainer.el).setView([lat, lng], zoom);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(this.map);
            this.marker = L.marker([lat, lng], { draggable: true }).addTo(this.map);
            this.circle = L.circle([lat, lng], { 
                radius: radius,
                color: '#3388ff', // Warna garis
                fillColor: '#3388ff', // Warna isi
                fillOpacity: 0.2 // Transparansi isi
            }).addTo(this.map);
            this.marker.on('dragend', () => this.updateCoordinates(this.marker.getLatLng()));
            this.map.on('click', (ev) => {
                this.marker.setLatLng(ev.latlng);
                this.updateCoordinates(ev.latlng);
            });
            
            // Panggil invalidateSize setelah inisialisasi pertama
            setTimeout(() => this.map.invalidateSize(), 150);
        } else {
            // Jika peta sudah ada, cukup update posisinya (lebih efisien)
            this.map.setView([lat, lng], zoom);
            this.marker.setLatLng([lat, lng]);
            this.circle.setLatLng([lat, lng]);
            this.circle.setRadius(radius);
        }
    }


    initializeMap() {
        if (!this.mapContainer.el) return;

        // --- PERBAIKAN 1: BACA KOORDINAT DARI RECORD ---
        // Ambil nilai latitude dan longitude yang sudah tersimpan di record.
        // Jika salah satu tidak ada, baru gunakan default (Jakarta).
        const hasExistingCoords = this.props.record.data.latitude && this.props.record.data.longitude;
        const lat = hasExistingCoords ? this.props.record.data.latitude : -6.2088;
        const lng = hasExistingCoords ? this.props.record.data.longitude : 106.8456;
        const zoom = hasExistingCoords ? 15 : 7;

        // --- PERBAIKAN 2: GUNAKAN TIMEOUT & INVALIDATESIZE ---
        // Menggunakan setTimeout untuk memastikan Odoo selesai merender layout-nya.
        setTimeout(() => {
            if (!this.mapContainer.el) return; // Safety check jika komponen sudah unmount

            // Inisialisasi peta
            this.map = L.map(this.mapContainer.el).setView([lat, lng], zoom);

            // Tambahkan layer peta
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            }).addTo(this.map);

            // Tambahkan marker
            this.marker = L.marker([lat, lng], { draggable: true }).addTo(this.map);

            // Set up event listeners
            this.marker.on('dragend', () => this.updateCoordinates(this.marker.getLatLng()));
            this.map.on('click', (ev) => {
                this.marker.setLatLng(ev.latlng);
                this.updateCoordinates(ev.latlng);
            });

            // SOLUSI KRITIS UNTUK LEBAR:
            // Setelah semuanya diinisialisasi, paksa Leaflet untuk menghitung ulang ukurannya.
            // Ini akan memperbaiki masalah lebar peta yang salah.
            this.map.invalidateSize();

        }, 150); // Sedikit menambah delay untuk keamanan
    }

    updateCoordinates(pos) {
        if (this.circle) {
            this.circle.setLatLng(pos);
        }
        this.props.record.update({
            latitude: pos.lat,
            longitude: pos.lng
        });
    }
}

// Pendaftaran ke registry (sudah benar dari sebelumnya)
registry.category("fields").add("location_picker", {
    component: LocationPicker,
    displayName: "Location Picker",
    supportedTypes: ["float", "char"], // Tetap mendukung float
});