const ID_RE = /^[A-Za-z0-9_-]{11}$/;
const HOSTS = new Set([
  "youtube.com",
  "www.youtube.com",
  "m.youtube.com",
  "music.youtube.com",
  "youtube-nocookie.com",
  "www.youtube-nocookie.com",
]);

/**
 * Early client-side extraction so the player can start while the backend indexes the video.
 * The backend re-validates everything; this only mirrors its accepted formats.
 */
export function parseVideoId(input: string): string | null {
  const value = input.trim();
  if (ID_RE.test(value)) return value;

  let url: URL;
  try {
    url = new URL(value.includes("://") ? value : `https://${value}`);
  } catch {
    return null;
  }
  const host = url.hostname.toLowerCase();
  const parts = url.pathname.split("/").filter(Boolean);
  let candidate: string | undefined;
  if (host === "youtu.be") candidate = parts[0];
  else if (HOSTS.has(host)) {
    if (parts[0] === "watch") candidate = url.searchParams.get("v") ?? undefined;
    else if (["shorts", "live", "embed", "v"].includes(parts[0] ?? "")) candidate = parts[1];
  }
  return candidate && ID_RE.test(candidate) ? candidate : null;
}
