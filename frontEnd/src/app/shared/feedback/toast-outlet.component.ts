import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { NotificationService } from './notification.service';

@Component({
  selector: 'app-toast-outlet',
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './toast-outlet.component.html',
  styleUrls: ['./toast-outlet.component.css'],
})
export class ToastOutletComponent {
  readonly notifications = inject(NotificationService);
}
