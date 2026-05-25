/**
 * Axios API client — all requests go through here.
 * Token is injected automatically from Zustand auth store.
 */
import axios from "axios";

export const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL
    ? `${process.env.NEXT_PUBLIC_API_URL}/api/v1`
    : "/api/v1",
  timeout: 60_000,
});

// Inject JWT token on every request
apiClient.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const stored = localStorage.getItem("autoradix-auth");
    if (stored) {
      try {
        const { state } = JSON.parse(stored);
        if (state?.token) {
          config.headers.Authorization = `Bearer ${state.token}`;
        }
      } catch {}
    }
  }
  return config;
});

// Global response error handler
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear auth and redirect to login
      if (typeof window !== "undefined") {
        localStorage.removeItem("autoradix-auth");
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);
