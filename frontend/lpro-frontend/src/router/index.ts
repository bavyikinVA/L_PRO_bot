import { createRouter, createWebHistory } from "vue-router";
import Service from "../views/Services.vue";
import Specialists from "../views/Specialists.vue";
import Booking from "../views/Booking.vue";
import BookingConfirm from "../views/BookingConfirm.vue";
import AdminPanel from "../views/AdminPanel.vue";
import AdminServices from "../views/admin/AdminServices.vue";
import AdminServiceCreate from "../views/admin/AdminServiceCreate.vue";
import AdminServiceUpdateSelect from "../views/admin/AdminServiceUpdateSelect.vue";
import AdminServiceEdit from "../views/admin/AdminServiceEdit.vue";
import AdminSpecialistCreate from "../views/admin/AdminSpecialistCreate.vue";
import AdminSpecialistUpdateSelect from "../views/admin/AdminSpecialistUpdateSelect.vue";
import AdminSpecialistEdit from "../views/admin/AdminSpecialistEdit.vue";
import AdminSpecialistServiceCreate from "../views/admin/AdminSpecialistServiceCreate.vue";
import AdminClientCreate from "../views/admin/AdminClientCreate.vue";
import AdminBookingCreate from "../views/admin/AdminBookingCreate.vue";
import AdminScheduleGenerate from "../views/admin/AdminScheduleGenerate.vue";
import { useAuthStore } from "../stores/authStore";

const routes = [
    { path: "/", name: "Home", component: Service },
    { path: "/services/:serviceId/specialists", name: "Specialists", component: Specialists },
    { path: "/services/:serviceId/specialists/:specialistId/booking", name: "Booking", component: Booking },
    { path: "/booking-confirm", name: "BookingConfirm", component: BookingConfirm },
    { path: "/admin", name: "AdminPanel", component: AdminPanel },
    { path: "/admin/services", name: "AdminServices", component: AdminServices },
    { path: "/admin/services/create", name: "AdminServiceCreate", component: AdminServiceCreate, },
    { path: "/admin/services/update", name: "AdminServiceUpdateSelect", component: AdminServiceUpdateSelect, },
    { path: "/admin/services/:serviceId/edit", name: "AdminServiceEdit", component: AdminServiceEdit, },
    { path: "/admin/specialists/create", name: "AdminSpecialistCreate", component: AdminSpecialistCreate, },
    { path: "/admin/specialists/update", name: "AdminSpecialistUpdateSelect", component: AdminSpecialistUpdateSelect,},
    { path: "/admin/specialists/:specialistId/edit", name: "AdminSpecialistEdit", component: AdminSpecialistEdit,},
    { path: "/admin/specialist-services/create", name: "AdminSpecialistServiceCreate", component: AdminSpecialistServiceCreate, },
    { path: "/admin/clients/create", name: "AdminClientCreate", component: AdminClientCreate},
    { path: "/admin/bookings/create", name: "AdminBookingCreate", component: AdminBookingCreate, },
    { path: "/admin/schedule/generate", name: "AdminScheduleGenerate", component: AdminScheduleGenerate, },
];

const router = createRouter({
    history: createWebHistory(),
    routes,
    scrollBehavior() {
        return { top: 0 };
    },
});

export default router;

router.beforeEach(async (to) => {
  if (!to.path.startsWith("/admin")) {
    return true;
  }

  if (to.path === "/admin") {
    return true;
  }

  const authStore = useAuthStore();
  const isAdmin = await authStore.checkAdmin();

  if (!isAdmin) {
    return "/admin";
  }

  return true;
});