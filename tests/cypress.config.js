const { defineConfig } = require("cypress");

module.exports = defineConfig({
  projectId: "vdyks4",
  e2e: {
    supportFile: false,
    baseUrl: "http://localhost:8081",
  },
});
