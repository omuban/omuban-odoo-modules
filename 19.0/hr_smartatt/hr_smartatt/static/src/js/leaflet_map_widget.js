/** @odoo-module **/

// Impor modul-modul yang dibutuhkan dari framework Odoo
import { AbstractField } from "@web/views/fields/abstract_field";
import { registry } from "@web/core/registry";
const { onMounted, onWillUnmount, useRef } = owl;

// Definisikan class untuk widget baru kita, mewarisi dari AbstractField
export class LeafletMapWidget extends AbstractField {
    // Tautkan class ini ke template XML-nya
    static template = "hr_smartatt.LeafletMapField";

    setup() {
        super.setup();

        // Buat referensi ke elemen DOM yang akan menjadi container peta
        this.mapContainer = useRef("mapContainer");

        // Variabel untuk menyimpan instance peta dan marker
        this.map = null;
        this.marker = null;

        // Hook yang akan dijalankan setelah komponen berhasil di-render di DOM
        onMounted(() => {
            console.log("LeafletMapWidget: onMounted hook triggered. Initializing map.");
            this.initializeMap();
        });

        // Hook yang akan dijalankan sebelum komponen dihancurkan (misal: saat pindah dari form view)
        onWillUnmount(() => {
            if (this.map) {
                this.map.remove();
            }
        });
    }

    // Fungsi utama untuk menginisialisasi peta Leaflet
    initializeMap() {
        if (!this.mapContainer.el) {
            console.error("LeafletMapWidget: Map container element not found!");
            return;
        }
        
        // Ambil nilai latitude/longitude dari record, atau gunakan default (Jakarta) jika kosong
        let lat = this.props.record.data.latitude || -6.200000;
        let lng = this.props.record.data.longitude || 106.816666;
        let zoom = this.props.record.data.latitude ? 15 : 7; // Zoom lebih dekat jika lokasi sudah ada

        // Buat instance peta dan arahkan ke container
        this.map = L.map(this.mapContainer.el).setView([lat, lng], zoom);

        // Tambahkan layer peta dasar dari OpenStreetMap
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(this.map);

        // Tambahkan marker (penanda) yang bisa diseret ke peta
        this.marker = L.marker([lat, lng], { draggable: true }).addTo(this.map);

        // --- Event Listeners ---
        // Saat marker selesai diseret
        this.marker.on('dragend', () => {
            const position = this.marker.getLatLng();
            this.updateCoordinates(position.lat, position.lng);
        });

        // Saat peta diklik
        this.map.on('click', (event) => {
            const position = event.latlng;
            this.marker.setLatLng(position); // Pindahkan marker ke lokasi klik
            this.updateCoordinates(position.lat, position.lng);
        });
    }
    
    // Fungsi untuk memperbarui nilai field 'latitude' dan 'longitude' di Odoo
    updateCoordinates(lat, lng) {
        this.props.record.update({
            latitude: lat,
            longitude: lng,
        });
    }
}

// Daftarkan widget baru kita ke dalam 'registry' field Odoo dengan nama 'leaflet_map'
registry.category("fields").add("leaflet_map", LeafletMapWidget);