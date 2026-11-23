import { ChangeDetectionStrategy, Component, DestroyRef, inject, output } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { AccessSession } from '../../core/access-session';
import { LoginRequest } from '../../core/login-request.service';

@Component({
  selector: 'app-review-access-form',
  imports: [FormsModule],
  providers: [LoginRequest],
  templateUrl: './review-access-form.component.html',
  host: { style: 'display: block' },
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ReviewAccessFormComponent {
  private readonly destroyRef = inject(DestroyRef);
  readonly loginRequest = inject(LoginRequest);
  readonly signedIn = output<AccessSession>();
  name = '';
  password = '';

  async login(): Promise<void> {
    if (this.loginRequest.busy() || !this.password || !this.name.trim()) {
      return;
    }

    try {
      const session = await this.loginRequest.submit('/api/review/login', {
        password: this.password,
        name: this.name,
      });
      if (session && !this.destroyRef.destroyed) {
        this.signedIn.emit(session);
      }
    } finally {
      this.password = '';
    }
  }
}
