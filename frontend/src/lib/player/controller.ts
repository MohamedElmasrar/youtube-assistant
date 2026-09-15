const POLL_MS = 250;
const STATE_PLAYING = 1; // YT.PlayerState.PLAYING

/**
 * Bridges the imperative YouTube player and React. Playback time lives here, outside React
 * state, so only components that subscribe (the transcript) re-render as the video plays.
 */
export class PlayerController {
  private player: YT.Player | null = null;
  private time = 0;
  private timer: ReturnType<typeof setInterval> | null = null;
  private listeners = new Set<() => void>();

  attach(player: YT.Player) {
    this.player = player;
  }

  detach() {
    this.stopPolling();
    this.player = null;
    this.setTime(0);
  }

  handleStateChange(state: number) {
    if (state === STATE_PLAYING) this.startPolling();
    else {
      this.stopPolling();
      this.readTime();
    }
  }

  seekTo(seconds: number) {
    if (!this.player) return;
    this.player.seekTo(seconds, true);
    this.player.playVideo();
    this.setTime(seconds);
  }

  getTime = () => this.time;

  subscribe = (listener: () => void) => {
    this.listeners.add(listener);
    return () => {
      this.listeners.delete(listener);
    };
  };

  private startPolling() {
    if (this.timer) return;
    this.timer = setInterval(() => this.readTime(), POLL_MS);
  }

  private stopPolling() {
    if (this.timer) clearInterval(this.timer);
    this.timer = null;
  }

  private readTime() {
    const current = this.player?.getCurrentTime?.();
    if (typeof current === "number") this.setTime(current);
  }

  private setTime(value: number) {
    if (value === this.time) return;
    this.time = value;
    this.listeners.forEach((listener) => listener());
  }
}
