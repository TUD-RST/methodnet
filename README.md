# Automatic Control Knowledge Based Assistance System (ACKBAS)

## General Information

This repository contains software which aims to support problem solving in the field of automatic control by providing suitable access to domain specific knowledge, e.g. in form of a method-network.

The user interface is implemented as an django web application.

Disclaimer: This software is still in early stage of development and not yet officially released.

## Development

- We use *NPM* for management of Javascript libraries.
- Install all dependencies (specified in `package.json`): `npm install` (in the main directory)
  - → This creates a directory `node_modules` which is comparable to the virtual env directory in python
- We use *webpack* to build a bundle (single file with own code and all dependencies) that is finally served as `/static/ackbas_core/main.js`.
- Own code lives in `ackbas_core/ts/index.ts` (typescript which will be compiled to JS during build).
- Build : run `npx webpack` after changing `ackbas_core/ts/index.ts`.
- `npm run build` does the same, due to the definitions in `package.json`.
- Also useful: `npm run start:dev` (start npm development server).

## Further relevant docs

- https://json-schema.org/understanding-json-schema/
