/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.CPCookieConsent = publicWidget.Widget.extend({
    selector: '#wrapwrap',

    start: function () {
        this.cookieName = 'cleanpresence_consent';
        // In Odoo 19, use this.$() for safer DOM access within widgets
        this.$banner = this.$('#cp_cookie_banner');
        
        this._checkConsent();
        this._bindEvents();
        return this._super.apply(this, arguments);
    },

    _bindEvents: function() {
        // Logic for Accept All
        this.$('#btn_accept_all').on('click', () => this._saveConsent(true, true));
        
        // Logic for Reject All
        this.$('#btn_reject_all').on('click', () => this._saveConsent(false, false));
        
        // Logic for Saving Preferences
        this.$('#btn_save_prefs').on('click', () => {
            const ana = this.$('#pref_analytics').is(':checked');
            const mar = this.$('#pref_marketing').is(':checked');
            this._saveConsent(ana, mar);
        });

        // Footer re-open (manual logic if needed, but data-bs-toggle is better)
        this.$('#reopen_cookie_settings').on('click', (e) => {
            e.preventDefault();
            this.$('#cookiePrefsModal').modal('show');
        });
    },

    _checkConsent: function() {
        const consent = this._getCookie(this.cookieName);
        if (!consent) {
            this.$banner.removeClass('d-none');
        } else {
            this._loadScripts(JSON.parse(consent));
        }
    },

    _saveConsent: function(analytics, marketing) {
        const consentData = {
            strictly_necessary: true,
            analytics: analytics,
            marketing: marketing,
            timestamp: new Date().toISOString()
        };
        const date = new Date();
        date.setTime(date.getTime() + (365 * 24 * 60 * 60 * 1000));
        document.cookie = `${this.cookieName}=${JSON.stringify(consentData)};expires=${date.toUTCString()};path=/;SameSite=Lax`;
        
        this.$banner.addClass('d-none');
        this._loadScripts(consentData);
    },

    _getCookie: function(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
    },

    _loadScripts: function(consent) {
        if (consent.analytics) {
            console.log("Analytics Active");
        }
        if (consent.marketing) {
            console.log("Marketing Active");
        }
    }
});