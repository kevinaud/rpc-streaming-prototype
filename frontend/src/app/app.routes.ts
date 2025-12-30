import { type Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./features/join-session/join-session.component').then((m) => m.JoinSessionComponent),
  },
  {
    path: 'session/:id',
    loadComponent: () =>
      import('./features/session/session.component').then((m) => m.SessionComponent),
  },
  {
    path: '**',
    redirectTo: '',
  },
];
