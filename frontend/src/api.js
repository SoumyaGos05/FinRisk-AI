/**
 * Central API configuration.
 *
 * All fetch/axios calls in this project must use `apiBase` as the URL prefix.
 * The value is read from the VITE_API_BASE_URL environment variable — never
 * hardcode "http://localhost:8000" anywhere else in the frontend.
 *
 * Set VITE_API_BASE_URL in frontend/.env (local) or your deployment environment.
 */

export const apiBase = import.meta.env.VITE_API_BASE_URL;
