/** @odoo-module **/

// File ini berisi fungsi-fungsi yang bisa digunakan bersama
// oleh beberapa komponen terkait platform.

export function getPlatformColor(platformName) {
    if (!platformName) return 'bg-secondary';
    const name = platformName.toLowerCase();
    if (name.includes('facebook')) return 'bg-primary';
    if (name.includes('instagram')) return 'bg-danger';
    if (name.includes('twitter') || name.includes('x.com')) return 'bg-dark';
    if (name.includes('linkedin')) return 'bg-info';
    if (name.includes('whatsapp')) return 'bg-success';
    return 'bg-secondary';
}

export function getPlatformIcon(platformName) {
    if (!platformName) return 'fa fa-globe';
    const name = platformName.toLowerCase();
    if (name.includes('facebook')) return 'fa fa-facebook-square';
    if (name.includes('instagram')) return 'fa fa-instagram';
    if (name.includes('twitter') || name.includes('x.com')) return 'fa fa-twitter';
    if (name.includes('linkedin')) return 'fa fa-linkedin-square';
    if (name.includes('whatsapp')) return 'fa fa-whatsapp';
    return 'fa fa-globe';
}