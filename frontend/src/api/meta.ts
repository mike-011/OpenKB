import { apiFetch } from "./client"

export interface Meta {
  version: string
  /** Build number stamp (YYYYMMDD-HHMM-NNN), "dev" for source checkouts (#81). */
  build: string
  /** Channel marker: "stable" | "dev" (default dev — all local builds are dev builds) (#81). */
  channel: string
}

/** App metadata (the real installed openkb version). */
export function getMeta(): Promise<Meta> {
  return apiFetch<Meta>("/api/v1/meta")
}
