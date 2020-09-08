const path = require('path');

module.exports = {
  mode: "development",
  optimization: {
    minimize: false
  },
  devtool: 'source-map',
  entry: './ackbas_core/js/index.js',
  output: {
    filename: 'main.js',
    path: path.resolve(__dirname, 'ackbas_core', 'static', 'ackbas_core'),
    publicPath: "/static/"
  },
};