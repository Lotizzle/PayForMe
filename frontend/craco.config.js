// craco.config.js
module.exports = {
  webpack: {
    configure: (webpackConfig) => {
      // Disable CSS minimizer (fixes Vercel build crash)
      webpackConfig.optimization.minimizer = webpackConfig.optimization.minimizer.filter(
        (plugin) => plugin.constructor.name !== 'CssMinimizerPlugin'
      );
      return webpackConfig;
    },
  },
};
