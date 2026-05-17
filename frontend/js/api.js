// MangoToon Frontend - API Client

const API = (function () {
  const BASE = "/api";

  async function request(method, path, body) {
    const opts = {
      method,
      headers: { "Content-Type": "application/json" },
    };
    if (body !== undefined) {
      opts.body = JSON.stringify(body);
    }

    let response;
    try {
      response = await fetch(BASE + path, opts);
    } catch (err) {
      throw new ApiError("Network error", "Could not reach the server", 0);
    }

    let data;
    try {
      data = await response.json();
    } catch {
      data = null;
    }

    if (!response.ok) {
      const detail = data?.detail || data?.error || response.statusText;
      throw new ApiError("Request failed", detail, response.status);
    }

    return data;
  }

  function get(path) {
    return request("GET", path);
  }

  function post(path, body) {
    return request("POST", path, body);
  }

  function del(path) {
    return request("DELETE", path);
  }

  class ApiError extends Error {
    constructor(message, detail, status) {
      super(message);
      this.name = "ApiError";
      this.detail = detail;
      this.status = status;
    }
  }

  return { get, post, del, ApiError, BASE };
})();
