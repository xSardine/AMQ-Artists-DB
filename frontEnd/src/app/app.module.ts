import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { SearchBarComponent } from './search-bar/search-bar.component';
import { SongTableComponent } from './song-table/song-table.component';
import { VimeModule } from '@vime/angular';
import { MatomoInitializationMode, NgxMatomoTrackerModule } from '@ngx-matomo/tracker';
import { NgxMatomoRouterModule } from '@ngx-matomo/router';

@NgModule({
  declarations: [
    AppComponent,
    SearchBarComponent,
    SongTableComponent,
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,
    BrowserAnimationsModule,
    VimeModule,
    NgxMatomoTrackerModule.forRoot({
      mode: MatomoInitializationMode.MANUAL,
    }),
    NgxMatomoRouterModule, // Only if you want to enable automatic page views tracking with @angular/router
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { }