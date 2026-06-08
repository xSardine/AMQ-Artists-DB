# Front End

Angular app for [AnisongDB](https://anisongdb.com), built with [Angular CLI](https://github.com/angular/angular-cli) **19** (see `package.json` for exact versions).

Most components are custom-built because I wanted to train on front end coding. The audio player uses [Vidstack](https://www.vidstack.io/).

## Development server

From the `frontEnd` folder:

```bash
npm install
npm start
```

Open `http://localhost:4200/`. The app reloads when you change source files.

If `npm install` fails on peer dependencies, try:

```bash
npm install --legacy-peer-deps
```

## API backend

You need a running API for the front end to display search results:
Dev server uses `127.0.0.1:8000` by default (you can change this to anisongdb.com if you don't want to start the backend).
To change this, edit `apiUrl` in `frontEnd/src/environments/environment.ts`.

Production builds use `frontEnd/src/environments/environment.prod.ts` instead (`ng build` swaps it in automatically via `angular.json`).

## Code scaffolding

Run `ng generate component component-name` to generate a new component. You can also use `ng generate directive|pipe|service|class|guard|interface|enum|module`.

## Build

Run `ng build` to build the project. The build artifacts will be stored in the `dist/` directory.

## Running unit tests

Run `ng test` to execute the unit tests via [Karma](https://karma-runner.github.io).

## Running end-to-end tests

Run `ng e2e` to execute the end-to-end tests via a platform of your choice. To use this command, you need to first add a package that implements end-to-end testing capabilities.

## Further help

To get more help on the Angular CLI use `ng help` or go check out the [Angular CLI Overview and Command Reference](https://angular.io/cli) page.
