# Front End

This project was generated with [Angular CLI](https://github.com/angular/angular-cli) version 12.2.5.

Most of the component are done from scratch because I wanted to train on front end coding, as it is something that I am not familiar with.

Exception is for the mp3 player: <https://github.com/vime-js/vime>

## Development server

TODO : Remove dependency to Vime by using a maintained library (Vidstack ?), and migrate to Angular 18.

There are dependencies problems, simply running `npm install` will not work. You need to install the dependencies like so :
Remove the folder `node_modules` if it exists and run the following commands :

```bash
npm ci --legacy-peer-deps
npm install @vime/core --force
```

Run `ng serve` for a dev server. Navigate to `http://localhost:4200/`. The app will automatically reload if you change any of the source files.

You need a working backend : Either run one locally following the instructions in the README.md of the backend folder, or use the one deployed on anisongdb.
The value to change is located in `AMQ-Artists-DB\frontEnd\src\app\core\services\search-request.service.ts`.

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
