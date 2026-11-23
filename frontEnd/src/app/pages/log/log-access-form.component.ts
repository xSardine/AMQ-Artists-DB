import { ChangeDetectionStrategy, Component, DestroyRef, inject, output } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { AccessSession } from '../../core/access-session';
import { LoginRequest } from '../../core/login-request.service';

@Component({
  selector: 'app-log-access-form',
  imports: [FormsModule],
  providers: [LoginRequest],
  templateUrl: './log-access-form.component.html',
  host: { style: 'display: block' },
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class LogAccessFormComponent {
  private readonly destroyRef = inject(DestroyRef);
  readonly loginRequest = inject(LoginRequest);
  readonly signedIn = output<AccessSession>();
  password = '';

  async login(): Promise<void> {
    if (this.loginRequest.busy() || !this.password) {
      return;
    }

    try {
      const session = await this.loginRequest.submit('/api/log/login', {
        password: this.password,
      });
      if (session && !this.destroyRef.destroyed) {
        this.signedIn.emit(session);
      }
    } finally {
      this.password = '';
    }
  }
}
