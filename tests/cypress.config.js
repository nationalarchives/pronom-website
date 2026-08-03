const { defineConfig } = require("cypress");
const webpackPreprocessor = require("@cypress/webpack-preprocessor");

module.exports = defineConfig({
  projectId: "vdyks4",
  e2e: {
    supportFile: false,
    baseUrl: "http://localhost:8081",
    setupNodeEvents(on) {
      on(
        "file:preprocessor",
        webpackPreprocessor({
          webpackOptions: {
            resolve: { extensions: [".ts", ".js"] },
            module: {
              rules: [
                {
                  test: /\.tsx?$/,
                  use: [
                    {
                      loader: "babel-loader",
                      options: {
                        presets: [
                          "@babel/preset-env",
                          "@babel/preset-typescript",
                        ],
                      },
                    },
                  ],
                  exclude: /node_modules/,
                },
              ],
            },
          },
        }),
      );
    },
  },
  allowCypressEnv: false,
});
