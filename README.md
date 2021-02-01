# Methodnet – A Formalized Representation of Control Theoretic Methods

Former name of the project: "Automatic Control Knowledge Based Assistance System (ACKBAS)"

## General Information

This repository contains software which aims to support problem solving in the field of automatic control by providing suitable access to domain specific knowledge, e.g. in form of a method-network.

The user interface is implemented as an django web application.

While code and interface are written in English, the contents of the method net are currently authored in German.


Disclaimer: This software is still in early stage of development and not yet officially released.

## Screenshot
![Screenshot showing web interface](screenshot.png)

## Development

- We use *NPM* for management of Javascript libraries.
- Install all dependencies (specified in `package.json`): `npm install` (in the main directory)
  - → This creates a directory `node_modules` which is comparable to the virtual env directory in python
- We use *esbuild* to build a bundle (single file with own code and all dependencies) that is finally served as `/static/ackbas_core/main.js`.
- Own code lives in `ackbas_core/ts/index.ts` (typescript which will be compiled to JS during build).
- Build : run `npm run build` after changing `ackbas_core/ts/index.ts`.

## Further relevant docs

- https://json-schema.org/understanding-json-schema/
