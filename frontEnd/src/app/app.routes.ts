import type { Routes } from '@angular/router';

export const routes: Routes = [
  { path: '', pathMatch: 'full', title: 'AnisongDB', loadComponent: () => import('./pages/search/search-page.component').then(m => m.SearchPageComponent) },
  { path: 'stats', title: 'Stats · AnisongDB', loadComponent: () => import('./pages/stats/stats-page.component').then(m => m.StatsPageComponent) },
  { path: 'log', title: 'Log · AnisongDB', loadComponent: () => import('./pages/log/log-page.component').then(m => m.LogPageComponent) },
  { path: 'contribute', title: 'Contribute · AnisongDB', loadComponent: () => import('./pages/contribute/contribute-page.component').then(m => m.ContributePageComponent) },
  { path: 'review', title: 'Review · AnisongDB', loadComponent: () => import('./pages/review/review-page.component').then(m => m.ReviewPageComponent) },
  { path: '**', title: 'Page not found · AnisongDB', loadComponent: () => import('./pages/not-found.component').then(m => m.NotFoundComponent) },
];
