# Automatic Control Knowledge Based Assistence System (ACKBAS)

## General Information

This repository contains software which aims to support problem solving in the field of automatic control by providing suitable access to domain specific knowledge, e.g. in form of a method-network.

The user interface is implemented as an django web application.


Disclaimer: This software is still in early stage of development and not yet officially released.

## Development

- uses NPM for management of Javascript libraries
- Webpack builds bundle that is finally served as `/static/ackbas_core/main.js`
- run `npx webpack` after changing `ackbas_core/js/index.js`