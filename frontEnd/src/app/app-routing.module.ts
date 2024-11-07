import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import {
  provideHttpClient,
  withInterceptorsFromDi,
} from '@angular/common/http';
import { SearchBarComponent } from './search-bar/search-bar.component';

const routes: Routes = [{ path: 'search', component: SearchBarComponent }];

@NgModule({
  exports: [RouterModule],
  imports: [RouterModule.forRoot(routes)],
  providers: [provideHttpClient(withInterceptorsFromDi())],
})
export class AppRoutingModule {}
