(function () {
  "use strict";
  const API_BASE = "https://tradinglab03-intake.maazxhasan.workers.dev";

  function element(tag, className, value) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (value !== undefined && value !== null) node.textContent = String(value);
    return node;
  }
  function formatNumber(value) {
    if (value === null || value === undefined || !Number.isFinite(Number(value))) return "—";
    return new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 }).format(Number(value));
  }
  function formatPercent(value) {
    if (value === null || value === undefined || !Number.isFinite(Number(value))) return "—";
    return (Number(value) * 100).toLocaleString("en-IN", { maximumFractionDigits: 1 }) + "%";
  }
  function prettyCategory(value) {
    return String(value || "other").replace(/_/g, " ").replace(/\b\w/g, function (c) { return c.toUpperCase(); });
  }
  function setStatus(root, message, kind) {
    const box = root.querySelector("[data-status]");
    if (!box) return;
    box.textContent = message;
    box.classList.remove("is-ok", "is-error", "is-warn");
    if (kind) box.classList.add("is-" + kind);
  }
  async function apiRequest(url, key, method) {
    const response = await fetch(url, {
      method: method || "GET",
      headers: {
        "Authorization": "Bearer " + key,
        "Accept": "application/json",
        ...(method && method !== "GET" ? { "Content-Type": "application/json" } : {})
      },
      ...(method && method !== "GET" ? { body: "{}" } : {}),
      mode: "cors",
      credentials: "omit",
      cache: "no-store"
    });
    const body = await response.json().catch(function () { return {}; });
    if (!response.ok) {
      if (response.status === 401) throw new Error("Owner key was rejected. Check the key and try again.");
      if (body && body.error_code === "ga4_not_configured") throw new Error("GA4 reporting is not configured yet. Add the GA4 property ID and service-account credentials to repository settings/secrets, then redeploy the Worker.");
      if (body && body.error) throw new Error(body.error);
      throw new Error("Analytics API returned HTTP " + response.status + ".");
    }
    return body;
  }
  function fillMetrics(root, data) {
    const metrics = data && data.metrics;
    const ai = data && data.ai_metrics;
    const values = {
      users: metrics ? metrics.total_users : null,
      sessions: metrics ? metrics.sessions : null,
      page_views: metrics ? metrics.page_views : null,
      engaged_sessions: metrics ? metrics.engaged_sessions : null,
      engagement_rate: metrics ? formatPercent(metrics.engagement_rate) : null,
      key_events: metrics ? metrics.key_events : null,
      conversion_sessions: metrics ? metrics.conversion_sessions : null,
      conversion_rate: metrics ? formatPercent(metrics.conversion_rate) : null,
      ai_conversion_rate: ai ? formatPercent(ai.conversion_rate) : null,
      ai_users: ai ? ai.total_users : null,
      ai_sessions: ai ? ai.sessions : null,
      ai_share: data && metrics ? formatPercent(data.ai_share_of_sessions) : null,
      ai_key_events: ai ? ai.key_events : null
    };
    root.querySelectorAll("[data-metric]").forEach(function (node) {
      const key = node.getAttribute("data-metric");
      const value = Object.prototype.hasOwnProperty.call(values, key) ? values[key] : null;
      node.textContent = value === null || value === undefined ? "—" : (typeof value === "string" ? value : formatNumber(value));
    });
    const periodLabel = root.querySelector("[data-period-label]");
    if (periodLabel) {
      periodLabel.textContent = data && data.from && data.to
        ? data.from + " to " + data.to + " · " + data.days + " days" + (data.property_timezone ? " · GA4 timezone: " + data.property_timezone : " · GA4 timezone not verified")
        : "No successful GA4 snapshot yet";
    }
    const syncLabel = root.querySelector("[data-sync-label]");
    if (syncLabel) {
      const sync = data && data.sync;
      syncLabel.textContent = sync
        ? "Last sync: " + (sync.finished_at || sync.started_at || "unknown time") + " · " + String(sync.status || "unknown").replace(/_/g, " ")
        : "Last successful sync: not available";
    }
    const warning = root.querySelector("[data-config-warning]");
    if (warning) {
      const messages = [];
      if (!data || !data.configuration || !data.configuration.api_configured) {
        messages.push("GA4 reporting is not connected yet. Configure the numeric GA4 property ID and service-account email/private key in GitHub Actions variables/secrets, deploy the Worker, and grant that service account Viewer access to this GA4 property.");
      } else if (!data.configuration.website_tracking_configured) {
        messages.push("Reporting credentials are configured, but the public website Measurement ID is not set. Add the verified G-… Measurement ID as the NEXORA_GA4_MEASUREMENT_ID repository variable. No fake visitor numbers are shown.");
      }
      if (data && data.message) messages.push(data.message);
      if (data && data.sync && data.sync.status === "success" && !data.property_timezone) messages.push("The latest successful sync has no recorded GA4 property timezone. Run a fresh sync after deploying the timezone validation update.");
      warning.textContent = messages.join(" ");
      warning.hidden = messages.length === 0;
    }
  }
  function renderBars(root, rows) {
    const target = root.querySelector("[data-trend]");
    if (!target) return;
    target.replaceChildren();
    if (!Array.isArray(rows) || !rows.length) {
      target.append(element("p", "va-empty", "No daily data is available yet."));
      return;
    }
    const values = rows.map(function (row) { return Math.max(0, Number(row.sessions) || 0); });
    const max = Math.max.apply(null, values.concat([1]));
    rows.forEach(function (row) {
      const group = element("div", "va-bar-item");
      const top = element("div", "va-bar-value", formatNumber(row.sessions));
      const barTrack = element("div", "va-bar-track");
      const bar = element("div", "va-bar-fill");
      const height = Math.max(3, (Math.max(0, Number(row.sessions) || 0) / max) * 100);
      bar.style.height = height + "%";
      bar.setAttribute("aria-label", formatNumber(row.sessions) + " sessions on " + row.date);
      barTrack.append(bar);
      const date = element("div", "va-bar-date", String(row.date || "").slice(5));
      group.append(top, barTrack, date);
      target.append(group);
    });
  }
  function renderRows(root, selector, rows, columns, emptyMessage) {
    const table = root.querySelector(selector);
    if (!table) return;
    table.replaceChildren();
    if (!Array.isArray(rows) || !rows.length) {
      const tr = element("tr");
      const td = element("td", "va-table-empty", emptyMessage);
      td.colSpan = columns.length;
      tr.append(td);
      table.append(tr);
      return;
    }
    rows.forEach(function (row) {
      const tr = element("tr");
      columns.forEach(function (column) {
        const td = element("td");
        let value = row[column.key];
        if (column.key === "source_category") value = prettyCategory(value);
        else if (column.key === "conversion_rate") value = formatPercent(value);
        else if (["sessions", "users", "page_views", "key_events", "conversion_sessions"].includes(column.key)) value = formatNumber(value);
        else if (column.key === "landing_path") value = String(value || "/");
        else value = value === null || value === undefined || value === "" ? "—" : value;
        td.textContent = String(value);
        if (column.key === "landing_path") td.className = "va-path";
        tr.append(td);
      });
      table.append(tr);
    });
  }
  function markSelectedPeriod(root, days) {
    root.querySelectorAll("[data-days]").forEach(function (button) {
      const active = Number(button.getAttribute("data-days")) === Number(days);
      button.classList.toggle("is-active", active);
      button.setAttribute("aria-pressed", active ? "true" : "false");
    });
  }
  async function load(root, doSync) {
    const keyInput = root.querySelector("[data-admin-key]");
    const key = keyInput ? keyInput.value.trim() : "";
    if (!key) {
      setStatus(root, "Enter the owner access key to load private analytics. This page does not save it.", "warn");
      if (keyInput) keyInput.focus();
      return;
    }
    const activePeriod = root.querySelector("[data-days].is-active");
    const days = activePeriod ? Number(activePeriod.getAttribute("data-days")) : 7;
    const loadButtons = root.querySelectorAll("[data-load], [data-sync]");
    loadButtons.forEach(function (button) { button.disabled = true; });
    try {
      if (doSync) {
        setStatus(root, "Requesting a GA4 refresh. This can take several seconds…", "");
        const sync = await apiRequest(API_BASE + "/api/admin/analytics/sync", key, "POST");
        if (!sync || sync.ok !== true) throw new Error((sync && sync.error_code) || "The GA4 refresh did not complete.");
        setStatus(root, "GA4 refresh completed through " + (sync.snapshot_date || "the latest available date") + ". Loading dashboard…", "ok");
      } else {
        setStatus(root, "Loading private visitor analytics…", "");
      }
      const data = await apiRequest(API_BASE + "/api/admin/analytics/visitors?days=" + encodeURIComponent(days), key, "GET");
      fillMetrics(root, data);
      renderBars(root, data.series || []);
      renderRows(root, "[data-table='sources']", data.sources || [], [
        { key: "source", label: "Source" }, { key: "medium", label: "Medium" },
        { key: "source_category", label: "Category" }, { key: "sessions", label: "Sessions" },
        { key: "users", label: "Users" }, { key: "key_events", label: "Key events" }, { key: "conversion_sessions", label: "Converting sessions" }, { key: "conversion_rate", label: "Conversion rate" }
      ], "No source breakdown is available.");
      renderRows(root, "[data-table='ai-sources']", data.ai_sources || [], [
        { key: "source", label: "AI platform/source" }, { key: "medium", label: "Medium" },
        { key: "sessions", label: "Sessions" }, { key: "users", label: "Users" }, { key: "key_events", label: "Key events" }, { key: "conversion_sessions", label: "Converting sessions" }, { key: "conversion_rate", label: "Conversion rate" }
      ], "No identifiable AI-platform referrals were recorded in this period.");
      renderRows(root, "[data-table='landing-pages']", data.landing_pages || [], [
        { key: "landing_path", label: "Landing page" }, { key: "source", label: "Source" },
        { key: "medium", label: "Medium" }, { key: "sessions", label: "Sessions" }, { key: "key_events", label: "Key events" }, { key: "conversion_sessions", label: "Converting sessions" }, { key: "conversion_rate", label: "Conversion rate" }
      ], "No landing-page data is available.");
      if (data && data.message && (!data.metrics || !data.configuration || !data.configuration.api_configured)) {
        setStatus(root, data.message, "warn");
      } else if (data && data.sync && data.sync.status === "success") {
        setStatus(root, "Analytics loaded successfully. Historical totals use GA4 range-level reports; daily values are not summed into unique users.", "ok");
      } else {
        setStatus(root, "Analytics loaded. Review the connection and sync status below.", "warn");
      }
    } catch (error) {
      setStatus(root, "Could not load analytics: " + String(error && error.message || "request failed"), "error");
    } finally {
      loadButtons.forEach(function (button) { button.disabled = false; });
    }
  }
  document.querySelectorAll("[data-visitor-analytics]").forEach(function (root) {
    root.querySelectorAll("[data-load]").forEach(function (button) {
      button.addEventListener("click", function () { load(root, false); });
    });
    root.querySelectorAll("[data-sync]").forEach(function (button) {
      button.addEventListener("click", function () { load(root, true); });
    });
    root.querySelectorAll("[data-days]").forEach(function (button) {
      button.addEventListener("click", function () {
        const days = Number(button.getAttribute("data-days"));
        markSelectedPeriod(root, days);
        const status = root.querySelector("[data-status]");
        if (status && root.querySelector("[data-admin-key]").value.trim()) load(root, false);
      });
    });
  });
})();