import { createApp } from "vue";

import App from "./App.vue";
import "./styles.css";
import { createAppRouter } from "./router";
import { registerModules } from "./modules";

registerModules();
const router = createAppRouter();

createApp(App).use(router).mount("#app");
