const modules = [];

export function registerModule(moduleDef) {
  if (!moduleDef || !moduleDef.name) {
    throw new Error("module must provide a name");
  }

  if (modules.some((item) => item.name === moduleDef.name)) {
    throw new Error(`duplicate module: ${moduleDef.name}`);
  }

  modules.push(moduleDef);
}

export function getRoutes() {
  return modules.flatMap((moduleDef) => moduleDef.routes || []);
}

export function getMenus() {
  return modules.flatMap((moduleDef) => moduleDef.menus || []);
}