let apiPromise: Promise<void> | null = null;

/** Load the YouTube IFrame Player API script once and resolve when `YT.Player` is usable. */
export function loadYouTubeApi(): Promise<void> {
  if (typeof window === "undefined") return new Promise(() => {});
  if (window.YT?.Player) return Promise.resolve();
  if (apiPromise) return apiPromise;

  apiPromise = new Promise<void>((resolve, reject) => {
    const previous = window.onYouTubeIframeAPIReady;
    window.onYouTubeIframeAPIReady = () => {
      previous?.();
      resolve();
    };
    const script = document.createElement("script");
    script.src = "https://www.youtube.com/iframe_api";
    script.async = true;
    script.onerror = () => {
      apiPromise = null;
      reject(new Error("Failed to load the YouTube player."));
    };
    document.head.appendChild(script);
  });
  return apiPromise;
}
