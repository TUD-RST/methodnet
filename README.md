# Automatic Control Knowledge Methodnet

## General Information

This repository contains software which aims to support problem solving in the field of automatic control by providing suitable access to domain specific knowledge, e.g. in form of a method-network.

The user interface is implemented as an django web application.

While code and interface are written in English, the contents of the method net are currently authored in German.


Disclaimer: This software is still in early stage of development and not yet officially released.

## Screenshot
![Screenshot showing web interface](screenshot.png)

## Development

- uses NPM for management of Javascript libraries
- Webpack builds bundle that is finally served as `/static/ackbas_core/main.js`
- Run `npm run build` after changing `ackbas_core/js/index.js`
- Alternatively, run `npm run watch` to start Webpack in watch mode. The typescript source will then automatically be recompiled when it changes.
