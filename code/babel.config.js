module.exports = (api) => {
  api.cache(true);

  const presets = [];
  const plugins = [
    "react-hot-loader/babel",
    "@babel/plugin-proposal-class-properties",
  ];

  return {
    presets,
    plugins,
  };
};
