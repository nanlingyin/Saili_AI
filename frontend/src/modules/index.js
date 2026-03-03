import { registerModule } from "../core/extensions";
import adminModule from "./admin";
import authModule from "./auth";
import competitionsModule from "./competitions";
import favoritesModule from "./favorites";
import forumModule from "./forum";
import profileModule from "./profile";
import recommendationsModule from "./recommendations";
import remindersModule from "./reminders";
import resumeModule from "./resume";
import sampleModule from "./sample";
import teamsModule from "./teams";

export function registerModules() {
  registerModule(authModule);
  registerModule(competitionsModule);
  registerModule(favoritesModule);
  registerModule(forumModule);
  registerModule(recommendationsModule);
  registerModule(remindersModule);
  registerModule(profileModule);
  registerModule(resumeModule);
  registerModule(teamsModule);
  registerModule(adminModule);
  registerModule(sampleModule);
}
