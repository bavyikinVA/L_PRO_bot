import { createRouter, createWebHistory } from "vue-router";
import Service from "../views/Services.vue";
import Specialists from "../views/Specialists.vue";
import Booking from "../views/Booking.vue";
import BookingConfirm from "../views/BookingConfirm.vue";

const routes = [
    { path: "/", name: "Home", component: Service },
    { path: "/services/:serviceId/specialists", name: "Specialists", component: Specialists },
    { path: "/services/:serviceId/specialists/:specialistId/booking", name: "Booking", component: Booking },
    { path: "/booking-confirm", name: "BookingConfirm", component: BookingConfirm },
];

const router = createRouter({
    history: createWebHistory(),
    routes,
    scrollBehavior() {
        return { top: 0 };
    },
});

export default router;