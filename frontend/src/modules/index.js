import { registerModule } from "../core/extensions";
import adminModule from "./admin";
import authModule from "./auth";
import competitionsModule from "./competitions";
import favoritesModule from "./favorites";
import recommendationsModule from "./recommendations";
import sampleModule from "./sample";

export function registerModules() {
  registerModule(authModule);
  registerModule(competitionsModule);
  registerModule(favoritesModule);
  registerModule(recommendationsModule);
  registerModule(adminModule);
  registerModule(sampleModule);
}
