# Front End

Frontend for [AnisongDB](https://anisongdb.com), built with **Angular 21**.

Audio playback uses [Vidstack](https://www.vidstack.io/). Statistics charts use [Chart.js](https://www.chartjs.org/).

## Pages

| Route | Description |
| --- | --- |
| `/` | Search anime songs and artist credits, play audio, and manage playlists. |
| `/stats` | Explore database statistics using charts and tables. |
| `/log` | Inspect recent API requests in a sortable table with selectable columns and full event details. Requires password. |
| `/contribute` | Suggest original anime, song, and artist names or artist IDs. |
| `/review` | Review contributions and view decision history. Requires password. |

## Development server

From the `frontEnd` folder:

```bash
npm install
npm start
```

Open `http://localhost:4200/`. All page routes above use this frontend address during development. The app reloads when you change source files.

## API backend

You need a running API for the front end to display search results.

Run the backend at `http://localhost:8000`. Development requests go directly to it. If you don't want to start the backend, you can set the `apiUrl` to `anisongdb.com` in `src/environments/environment.ts`

Production builds use `src/environments/environment.prod.ts` instead, selected automatically by `angular.json`.
