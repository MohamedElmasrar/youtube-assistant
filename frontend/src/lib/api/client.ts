import type { z } from "zod";
import { API_URL } from "@/lib/config";

export class ApiError extends Error {
  constructor(
    message: string,
    readonly code: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

/** Fetch a custom REST endpoint and validate the response against a schema. */
export async function apiRequest<S extends z.ZodType>(
  path: string,
  schema: S,
  init: RequestInit = {},
): Promise<z.infer<S>> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...init.headers },
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") throw error;
    throw new ApiError(
      "Cannot reach the backend. Is `langgraph dev` running?",
      "network_error",
      0,
    );
  }

  const body: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    const envelope = (body as { error?: { code?: string; message?: string } } | null)?.error;
    throw new ApiError(
      envelope?.message ?? `Request failed (${response.status})`,
      envelope?.code ?? "request_failed",
      response.status,
    );
  }
  const parsed = schema.safeParse(body);
  if (!parsed.success) {
    throw new ApiError("The backend returned an unexpected response.", "invalid_response", 502);
  }
  return parsed.data;
}
