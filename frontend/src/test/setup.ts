import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach, vi } from "vitest";

afterEach(() => {
  cleanup();
  window.localStorage.clear();
  vi.clearAllMocks();
});

// jsdom lacks these browser APIs used by the UI.
window.matchMedia ??= ((query: string) => ({
  matches: true,
  media: query,
  addEventListener: () => {},
  removeEventListener: () => {},
})) as unknown as typeof window.matchMedia;

class ResizeObserverStub {
  observe() {}
  unobserve() {}
  disconnect() {}
}
globalThis.ResizeObserver ??= ResizeObserverStub;
Element.prototype.scrollTo ??= () => {};
Element.prototype.getAnimations ??= () => [];
