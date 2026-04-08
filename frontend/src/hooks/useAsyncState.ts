import { useState } from "react";

export type AsyncState = {
  loading: boolean;
  status: string;
  error: string;
};

export function useAsyncState(initialStatus = "") {
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState(initialStatus);
  const [error, setError] = useState("");

  function start(message: string) {
    setLoading(true);
    setStatus(message);
    setError("");
  }

  function succeed(message = "") {
    setLoading(false);
    setStatus(message);
    setError("");
  }

  function fail(message: string) {
    setLoading(false);
    setError(message);
    setStatus("");
  }

  function reset() {
    setLoading(false);
    setStatus("");
    setError("");
  }

  return {
    loading,
    status,
    error,
    start,
    succeed,
    fail,
    reset,
  };
}
