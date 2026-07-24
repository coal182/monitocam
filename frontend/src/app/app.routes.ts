import { Routes } from '@angular/router';
import { authGuard, publicGuard } from './core/auth.guard';
import { LoginComponent } from './features/auth/login.component';
import { CamerasComponent } from './features/cameras/cameras.component';
import { RecordingsComponent } from './features/recordings/recordings.component';

export const routes: Routes = [
  {
    path: 'login',
    component: LoginComponent,
    canActivate: [publicGuard]
  },
  {
    path: '',
    component: RecordingsComponent,
    canActivate: [authGuard]
  },
  {
    path: 'recordings',
    redirectTo: ''
  },
  {
    path: 'cameras',
    component: CamerasComponent,
    canActivate: [authGuard]
  },
  {
    path: '**',
    redirectTo: ''
  }
];
