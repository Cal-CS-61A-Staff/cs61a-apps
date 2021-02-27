const webpack = require("webpack");
const path = require("path");
const HtmlWebpackPlugin = require("html-webpack-plugin");
const HtmlWebpackTagsPlugin = require("html-webpack-tags-plugin");
const MonacoWebpackPlugin = require("monaco-editor-webpack-plugin");
const CopyWebpackPlugin = require("copy-webpack-plugin");
const WorkboxPlugin = require("workbox-webpack-plugin");

module.exports = (env) => ({
  entry: {
    main: "./src/renderer/index.js",
    pythonWorker: "./src/web/pythonWorker.js",
    sqlWorker: "./src/languages/sql/web/sqlWorker.js",
    webConsoleWorker: "./src/web/webConsole/webConsoleWorker.js",
  },
  output: {
    filename: "static/[name].js",
    path: path.resolve(__dirname, "dist/web/"),
    globalObject: "this", // workaround for HMR, https://github.com/webpack/webpack/issues/6642
    publicPath: "/",
  },
  devtool: "source-map",
  devServer: {
    contentBase: path.resolve(__dirname, "dist/web/static/"),
    proxy: {
      "/api": {
        target: "http://localhost:5000",
        secure: false,
      },
    },
  },
  module: {
    noParse: /monaco-editor\/min\/vs\/loader\.js|jquery\.jsPlumb-1\.3\.10-all-min\.js/,
    rules: [
      {
        test: /.jsx?$/,
        loader: "babel-loader",
        exclude: /node_modules/,
        query: {
          presets: ["@babel/react"],
        },
      },
      {
        test: /\.css$/,
        use: [{ loader: "style-loader" }, { loader: "css-loader" }],
      },
      {
        test: /\.(eot|woff|woff2|ttf|svg|png|jpe?g|gif)(\?\S*)?$/,
        loader: "url-loader",
      },
      {
        test: /\.py$/i,
        use: "raw-loader",
      },
      {
        test: /\.js$/,
        exclude: /node_modules/,
        loader: "eslint-loader",
        options: {
          emitError: true,
          emitWarning: true,
        },
      },
    ],
  },
  plugins: [
    new HtmlWebpackPlugin({
      title: "61A Code",
      excludeChunks: ["pythonWorker", "webConsoleWorker", "sqlWorker"],
      favicon: "./static/favicon.ico",
      filename: "./static/index.html",
      template: "./build/index.html",
    }),
    new HtmlWebpackTagsPlugin({
      tags: ["static/pace/pace.min.js", "static/pace/pace.css"],
      append: false,
    }),
    new webpack.DefinePlugin({
      ELECTRON: false,
      SCHEME_COMPILE: (env && env.SCHEME_COMPILE) || false,
      __static: JSON.stringify("/static"),
      VERSION: '"2.2.1"',
    }),
    new MonacoWebpackPlugin({
      output: "./static",
      languages: ["python", "scheme", "sql"],
    }),
    new webpack.ProvidePlugin({
      $: "jquery",
      jQuery: "jquery",
      jquery: "jquery",
    }),
    new CopyWebpackPlugin([
      {
        from: "static",
        to: "static",
        ignore: ["IGNORE*"],
      },
      {
        from: "src/web-server",
        to: ".",
      },
    ]),
    new WorkboxPlugin.GenerateSW({
      swDest: "static/service-worker.js",
      exclude: [/.*/],
      importsDirectory: "static",
      runtimeCaching: [
        {
          urlPattern: ({ url }) => !url.pathname.match(/\/?(oauth|data).*/),
          handler: "StaleWhileRevalidate",
        },
      ],
    }),
  ],
});
