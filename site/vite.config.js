import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  // GitHub Pages serves a project site from /<repository>/ until a custom domain is
  // connected. The deploy build passes that path in; everywhere else the site sits at
  // the root.
  base: process.env.SITE_BASE || "/",
  plugins: [react()],
});
