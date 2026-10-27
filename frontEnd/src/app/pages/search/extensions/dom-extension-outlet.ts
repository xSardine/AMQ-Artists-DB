type DomExtensionCleanup = () => void;
type DomExtensionRender = (
  container: HTMLElement,
) => void | DomExtensionCleanup;

/** Owns DOM and cleanup callbacks created by a userscript renderer. */
export class DomExtensionOutlet {
  private cleanup?: DomExtensionCleanup;
  private description?: string;

  constructor(private readonly container: HTMLElement) {}

  mount(description: string, render: DomExtensionRender): boolean {
    this.unmount();
    this.description = description;

    try {
      const cleanup = render(this.container);
      this.cleanup = typeof cleanup === 'function' ? cleanup : undefined;
      return true;
    } catch (error) {
      this.container.replaceChildren();
      this.description = undefined;
      console.error(`Could not render ${description}.`, error);
      return false;
    }
  }

  unmount(): void {
    try {
      this.cleanup?.();
    } catch (error) {
      console.error(
        `Could not clean up ${this.description ?? 'userscript content'}.`,
        error,
      );
    }

    this.container.replaceChildren();
    this.cleanup = undefined;
    this.description = undefined;
  }
}
