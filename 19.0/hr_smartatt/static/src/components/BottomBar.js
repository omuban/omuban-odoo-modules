/** @odoo-module **/
import { Component, xml } from "@odoo/owl";

export class BottomBar extends Component {
    static props = {
        currentPage: { type: String },
        onNavigate: { type: Function },
    };

    static template = xml`
        <nav class="bottom-bar">
            <nav class="bottom-bar">
            <!-- PERBAIKAN: Tambahkan kelas 'bottom-bar-item' -->
            <button t-on-click="() => props.onNavigate('dashboard')" 
                    class="bottom-bar-item"
                    t-att-class="{ 'active': props.currentPage === 'dashboard' }">
                <i class="fa fa-home fa-lg"/>
                <span>Home</span>
            </button>
            <button t-on-click="() => props.onNavigate('history')" 
                    class="bottom-bar-item"
                    t-att-class="{ 'active': props.currentPage === 'history' }">
                <i class="fa fa-history fa-lg"/>
                <span>History</span>
            </button>
            <button t-on-click="() => props.onNavigate('account')" 
                    class="bottom-bar-item"
                    t-att-class="{ 'active': props.currentPage === 'account' }">
                <i class="fa fa-user fa-lg"/>
                <span>Account</span>
            </button>
        </nav>
        </nav>
    `;
}