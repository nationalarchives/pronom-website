import { defineConfig } from "vite";

export default defineConfig({
  input: "src/scripts/main.mjs",
  build: {
    sourcemap: true,
    outDir: ".",
    assetsDir: "assets",
    emptyOutDir: false,
    rolldownOptions: {
      output: {
        entryFileNames: "assets/[name].js",
      },
    },
  },
});
