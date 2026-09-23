const JSON_HEADERS = {
  "content-type": "application/json; charset=utf-8",
  "cache-control": "no-store",
};

const HTML_HEADERS = {
  "content-type": "text/html; charset=utf-8",
  "x-content-type-options": "nosniff",
  "referrer-policy": "no-referrer",
};

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (request.method === "POST" && url.pathname === "/api/publish/plan") {
      return publishPlan(request, env);
    }

    if (request.method === "GET" && url.pathname.startsWith("/p/")) {
      return showPublicPlan(request, decodeURIComponent(url.pathname.slice(3)), env);
    }

    if (request.method === "GET" && url.pathname === "/oauth/intervals/start") {
      return oauthIntervalsStart(request, env);
    }

    if (request.method === "GET" && url.pathname === "/oauth/intervals/callback") {
      return oauthIntervalsCallback(request, env);
    }

    if (request.method === "POST" && url.pathname === "/api/deliver/plan") {
      return deliverPlan(request, env);
    }

    if (request.method === "GET" && url.pathname === "/privacy") {
      return htmlResponse(renderPrivacy());
    }

    if (request.method === "GET" && url.pathname === "/") {
      return htmlResponse(renderHome());
    }

    return new Response("Not found", { status: 404 });
  },
};

async function publishPlan(request, env) {
  if (!env.WOL_PUBLISHER_KEY) {
    return jsonResponse({ error: "publisher_not_configured" }, 503);
  }

  const suppliedKey = readBearerToken(request);
  if (!suppliedKey || !safeEqual(suppliedKey, env.WOL_PUBLISHER_KEY)) {
    return jsonResponse({ error: "unauthorized" }, 401);
  }

  let payload;
  try {
    payload = await request.json();
  } catch {
    return jsonResponse({ error: "invalid_json" }, 400);
  }

  const validation = validatePlan(payload);
  if (!validation.ok) {
    return jsonResponse(
      { error: "invalid_plan", details: validation.errors },
      400,
    );
  }

  const publicId = randomPublicId();
  const createdAt = new Date().toISOString();

  try {
    const insertPlan = await env.DB.prepare(
      "INSERT INTO public_plans (public_id, title, description, status, version, created_at) VALUES (?, ?, ?, 'published', 1, ?)",
    )
      .bind(
        publicId,
        payload.title.trim(),
        normalizeOptionalText(payload.description),
        createdAt,
      )
      .run();

    if (!insertPlan.success) {
      throw new Error("Unable to insert public plan");
    }

    const plan = await env.DB.prepare(
      "SELECT id FROM public_plans WHERE public_id = ?",
    )
      .bind(publicId)
      .first();

    if (!plan?.id) {
      throw new Error("Unable to resolve created plan");
    }

    const statements = payload.items.map((item, index) =>
      env.DB.prepare(
        "INSERT INTO plan_items (plan_id, item_id, day_offset, display_order, workout_snapshot) VALUES (?, ?, ?, ?, ?)",
      ).bind(
        plan.id,
        item.item_id || crypto.randomUUID(),
        item.day_offset,
        Number.isInteger(item.display_order) ? item.display_order : index,
        JSON.stringify(item.workout),
      ),
    );

    if (statements.length) {
      await env.DB.batch(statements);
    }

    const origin = new URL(request.url).origin;
    return jsonResponse(
      {
        public_id: publicId,
        url: origin + "/p/" + encodeURIComponent(publicId),
      },
      201,
    );
  } catch (error) {
    console.error("publishPlan failed", error);
    return jsonResponse({ error: "storage_error" }, 500);
  }
}

async function showPublicPlan(request, publicId, env) {
  if (!publicId || publicId.length > 128) {
    return new Response("Not found", { status: 404 });
  }

  const plan = await env.DB.prepare(
    "SELECT id, public_id, title, description, status, version, created_at FROM public_plans WHERE public_id = ?",
  )
    .bind(publicId)
    .first();

  if (!plan || plan.status !== "published") {
    return new Response("Not found", { status: 404 });
  }

  const { results } = await env.DB.prepare(
    "SELECT item_id, day_offset, display_order, workout_snapshot FROM plan_items WHERE plan_id = ? ORDER BY day_offset ASC, display_order ASC, id ASC",
  )
    .bind(plan.id)
    .all();

  const items = [];
  for (const row of results || []) {
    try {
      items.push({
        item_id: row.item_id,
        day_offset: row.day_offset,
        display_order: row.display_order,
        workout: JSON.parse(row.workout_snapshot),
      });
    } catch {
      items.push({
        item_id: row.item_id,
        day_offset: row.day_offset,
        display_order: row.display_order,
        workout: { name: "Workout" },
      });
    }
  }

  const oauthConfigured = Boolean(
    env.INTERVALS_CLIENT_ID &&
    env.INTERVALS_CLIENT_SECRET &&
    env.SESSION_SECRET
  );

  return htmlResponse(renderPlanPage(plan, items, oauthConfigured));
}

async function oauthIntervalsStart(request, env) {
  if (!oauthReady(env)) {
    return htmlResponse(renderSetupPending(), 503);
  }

  const url = new URL(request.url);
  const publicId = url.searchParams.get("public_id") || "";
  const weekStart = url.searchParams.get("week_start") || "";
  const destination = url.searchParams.get("destination") || "";

  if (!(await publicPlanExists(publicId, env))) {
    return jsonResponse({ error: "plan_not_found" }, 404);
  }

  if (!isValidMondayDate(weekStart)) {
    return jsonResponse({ error: "invalid_week_start" }, 400);
  }

  if (!["garmin", "suunto"].includes(destination)) {
    return jsonResponse({ error: "invalid_destination" }, 400);
  }

  let sessionId = readCookie(request, "wol_session");
  const isNewSession = !sessionId;
  if (!sessionId) {
    sessionId = randomToken(24);
  }

  const now = new Date().toISOString();
  await env.DB.prepare(
    "INSERT OR IGNORE INTO athlete_sessions (session_id, created_at, updated_at) VALUES (?, ?, ?)"
  ).bind(sessionId, now, now).run();

  const state = randomToken(32);
  await env.DB.prepare(
    "INSERT INTO oauth_states (state, session_id, public_id, week_start, destination, created_at) VALUES (?, ?, ?, ?, ?, ?)"
  ).bind(state, sessionId, publicId, weekStart, destination, now).run();

  const redirectUri = url.origin + "/oauth/intervals/callback";
  const authorize = new URL("https://intervals.icu/oauth/authorize");
  authorize.searchParams.set("client_id", env.INTERVALS_CLIENT_ID);
  authorize.searchParams.set("redirect_uri", redirectUri);
  authorize.searchParams.set("scope", "CALENDAR:WRITE");
  authorize.searchParams.set("state", state);

  const headers = new Headers({ location: authorize.toString() });
  if (isNewSession) {
    headers.append("set-cookie", buildSessionCookie(sessionId, url.protocol === "https:"));
  }

  return new Response(null, { status: 302, headers });
}

async function oauthIntervalsCallback(request, env) {
  if (!oauthReady(env)) {
    return htmlResponse(renderSetupPending(), 503);
  }

  const url = new URL(request.url);
  const error = url.searchParams.get("error");
  if (error) {
    return htmlResponse(renderOAuthError(error), 400);
  }

  const code = url.searchParams.get("code") || "";
  const state = url.searchParams.get("state") || "";
  if (!code || !state) {
    return jsonResponse({ error: "missing_code_or_state" }, 400);
  }

  const saved = await env.DB.prepare(
    "SELECT state, session_id, public_id, week_start, destination, created_at FROM oauth_states WHERE state = ?"
  ).bind(state).first();

  if (!saved) {
    return jsonResponse({ error: "invalid_oauth_state" }, 400);
  }

  const stateAgeMs = Date.now() - Date.parse(saved.created_at);
  if (!Number.isFinite(stateAgeMs) || stateAgeMs < 0 || stateAgeMs > 10 * 60 * 1000) {
    await env.DB.prepare("DELETE FROM oauth_states WHERE state = ?").bind(state).run();
    return jsonResponse({ error: "expired_oauth_state" }, 400);
  }

  const cookieSession = readCookie(request, "wol_session");
  if (!cookieSession || !safeEqual(cookieSession, saved.session_id)) {
    return jsonResponse({ error: "oauth_session_mismatch" }, 400);
  }

  const form = new URLSearchParams();
  form.set("client_id", env.INTERVALS_CLIENT_ID);
  form.set("client_secret", env.INTERVALS_CLIENT_SECRET);
  form.set("code", code);

  const tokenResponse = await fetch("https://intervals.icu/api/oauth/token", {
    method: "POST",
    headers: { "content-type": "application/x-www-form-urlencoded" },
    body: form,
  });

  if (!tokenResponse.ok) {
    console.error("Intervals token exchange failed", tokenResponse.status);
    return htmlResponse(renderOAuthError("token_exchange_failed"), 502);
  }

  const tokenData = await tokenResponse.json();
  if (!tokenData.access_token || !tokenData.athlete?.id) {
    return htmlResponse(renderOAuthError("invalid_token_response"), 502);
  }

  const encryptedToken = await encryptSecret(tokenData.access_token, env.SESSION_SECRET);
  const updatedAt = new Date().toISOString();

  await env.DB.prepare(
    "UPDATE athlete_sessions SET intervals_athlete_id = ?, access_token_encrypted = ?, granted_scopes = ?, updated_at = ? WHERE session_id = ?"
  ).bind(
    String(tokenData.athlete.id),
    encryptedToken,
    String(tokenData.scope || ""),
    updatedAt,
    saved.session_id
  ).run();

  await env.DB.prepare("DELETE FROM oauth_states WHERE state = ?").bind(state).run();

  const returnUrl = new URL("/p/" + encodeURIComponent(saved.public_id), url.origin);
  returnUrl.searchParams.set("connected", "1");
  returnUrl.searchParams.set("week_start", saved.week_start);
  returnUrl.searchParams.set("destination", saved.destination);

  return Response.redirect(returnUrl.toString(), 302);
}

async function deliverPlan(request, env) {
  if (!oauthReady(env)) {
    return jsonResponse({ error: "oauth_not_configured" }, 503);
  }

  const sessionId = readCookie(request, "wol_session");
  if (!sessionId) {
    return jsonResponse({ error: "intervals_not_connected" }, 401);
  }

  let payload;
  try {
    payload = await request.json();
  } catch {
    return jsonResponse({ error: "invalid_json" }, 400);
  }

  const publicId = typeof payload.public_id === "string" ? payload.public_id : "";
  const weekStart = typeof payload.week_start === "string" ? payload.week_start : "";
  const destination = typeof payload.destination === "string" ? payload.destination : "";

  if (!isValidMondayDate(weekStart)) {
    return jsonResponse({ error: "invalid_week_start" }, 400);
  }

  if (!["garmin", "suunto"].includes(destination)) {
    return jsonResponse({ error: "invalid_destination" }, 400);
  }

  const session = await env.DB.prepare(
    "SELECT intervals_athlete_id, access_token_encrypted, granted_scopes FROM athlete_sessions WHERE session_id = ?"
  ).bind(sessionId).first();

  if (!session?.access_token_encrypted) {
    return jsonResponse({ error: "intervals_not_connected" }, 401);
  }

  const scopes = String(session.granted_scopes || "").split(",").map((s) => s.trim());
  if (!scopes.includes("CALENDAR:WRITE")) {
    return jsonResponse({ error: "calendar_write_scope_missing" }, 403);
  }

  const plan = await env.DB.prepare(
    "SELECT id, title, status FROM public_plans WHERE public_id = ?"
  ).bind(publicId).first();

  if (!plan || plan.status !== "published") {
    return jsonResponse({ error: "plan_not_found" }, 404);
  }

  const { results } = await env.DB.prepare(
    "SELECT item_id, day_offset, workout_snapshot FROM plan_items WHERE plan_id = ? ORDER BY day_offset ASC, display_order ASC, id ASC"
  ).bind(plan.id).all();

  if (!results?.length) {
    return jsonResponse({ error: "empty_plan" }, 400);
  }

  const events = [];
  try {
    for (const row of results) {
      const workout = JSON.parse(row.workout_snapshot);
      const date = addDaysToIsoDate(weekStart, row.day_offset);
      events.push({
        category: "WORKOUT",
        start_date_local: date + "T00:00:00",
        type: "Run",
        name: workoutName(workout),
        description: buildIntervalsWorkoutSnapshot(workout),
        external_id: "wol:" + publicId + ":" + row.item_id + ":" + date,
      });
    }
  } catch (error) {
    console.error("Workout conversion failed", error);
    return jsonResponse({ error: "unsupported_workout", details: String(error.message || error) }, 400);
  }

  let accessToken;
  try {
    accessToken = await decryptSecret(session.access_token_encrypted, env.SESSION_SECRET);
  } catch (error) {
    console.error("Token decrypt failed", error);
    return jsonResponse({ error: "stored_token_invalid" }, 500);
  }

  const intervalsResponse = await fetch(
    "https://intervals.icu/api/v1/athlete/0/events/bulk?upsert=true",
    {
      method: "POST",
      headers: {
        authorization: "Bearer " + accessToken,
        "content-type": "application/json",
      },
      body: JSON.stringify(events),
    }
  );

  if (intervalsResponse.status === 401 || intervalsResponse.status === 403) {
    return jsonResponse({ error: "intervals_authorization_failed" }, 401);
  }

  if (!intervalsResponse.ok) {
    const errorText = await intervalsResponse.text();
    console.error("Intervals bulk delivery failed", intervalsResponse.status, errorText.slice(0, 500));
    return jsonResponse({ error: "intervals_delivery_failed", status: intervalsResponse.status }, 502);
  }

  const delivered = await intervalsResponse.json();
  return jsonResponse({
    ok: true,
    destination,
    events: Array.isArray(delivered) ? delivered.length : events.length,
  });
}

function buildIntervalsWorkoutSnapshot(workout) {
  if (!workout || typeof workout !== "object" || Array.isArray(workout)) {
    throw new Error("Workout snapshot must be an object");
  }

  if (!Array.isArray(workout.steps) || workout.steps.length === 0) {
    throw new Error("Workout snapshot must contain steps");
  }

  const lines = [];
  for (const item of workout.steps) {
    if (item && Number.isInteger(item.repetitions) && Array.isArray(item.steps)) {
      if (item.repetitions <= 0 || item.steps.length === 0) {
        throw new Error("Invalid repeat block");
      }
      lines.push(String(item.repetitions) + "x");
      for (const step of item.steps) {
        lines.push(buildIntervalsStepSnapshot(step));
      }
      continue;
    }

    lines.push(buildIntervalsStepSnapshot(item));
  }

  return lines.join("\n");
}

function buildIntervalsStepSnapshot(step) {
  if (!step || typeof step !== "object" || Array.isArray(step)) {
    throw new Error("Invalid workout step");
  }

  if (step.end_type === "lap_button") {
    throw new Error("Intervals.icu export: LAP button is not yet validated");
  }

  let duration;
  if (step.end_type === "time") {
    const seconds = Number(step.value);
    if (!(seconds > 0)) throw new Error("Invalid time step value");
    duration = Number.isInteger(seconds) && seconds % 60 === 0
      ? String(seconds / 60) + "m"
      : formatNumber(seconds) + "s";
  } else if (step.end_type === "distance") {
    const meters = Number(step.value);
    if (!(meters > 0)) throw new Error("Invalid distance step value");
    duration = step.preferred_unit === "km"
      ? formatNumber(meters / 1000) + "km"
      : formatNumber(meters) + "m";
  } else {
    throw new Error("Unsupported end type: " + String(step.end_type));
  }

  const target = step.target || { kind: "none" };
  let targetText = "";
  if (target.kind === "heart_rate_zone") {
    targetText = " Z" + Number(target.zone_number) + " HR";
  } else if (target.kind === "heart_rate_range") {
    targetText = " " + Number(target.min_bpm) + "-" + Number(target.max_bpm) + " HR";
  } else if (target.kind === "pace_range") {
    targetText =
      " " +
      formatPace(target.pace_fast_seconds_per_km) +
      "-" +
      formatPace(target.pace_slow_seconds_per_km) +
      " Pace";
  } else if (target.kind !== "none") {
    throw new Error("Unsupported target kind: " + String(target.kind));
  }

  const intensityByRole = {
    warmup: "warmup",
    interval: "interval",
    recovery: "recovery",
    cooldown: "cooldown",
  };
  const intensity = intensityByRole[step.role];
  const intensityText = intensity ? " intensity=" + intensity : "";

  return "- " + duration + targetText + intensityText;
}

function formatNumber(value) {
  const number = Number(value);
  return Number.isInteger(number) ? String(number) : String(number);
}

function formatPace(secondsPerKm) {
  const seconds = Math.round(Number(secondsPerKm));
  if (!(seconds > 0)) throw new Error("Invalid pace target");
  const minutes = Math.floor(seconds / 60);
  const remainder = seconds % 60;
  return String(minutes) + ":" + String(remainder).padStart(2, "0");
}

function oauthReady(env) {
  return Boolean(
    env.INTERVALS_CLIENT_ID &&
    env.INTERVALS_CLIENT_SECRET &&
    env.SESSION_SECRET
  );
}

async function publicPlanExists(publicId, env) {
  if (!publicId) return false;
  const row = await env.DB.prepare(
    "SELECT 1 AS ok FROM public_plans WHERE public_id = ? AND status = 'published'"
  ).bind(publicId).first();
  return Boolean(row?.ok);
}

function isValidMondayDate(value) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
  const date = new Date(value + "T00:00:00Z");
  return !Number.isNaN(date.getTime()) && date.getUTCDay() === 1;
}

function addDaysToIsoDate(value, days) {
  const date = new Date(value + "T00:00:00Z");
  date.setUTCDate(date.getUTCDate() + Number(days));
  return date.toISOString().slice(0, 10);
}

function readCookie(request, name) {
  const cookie = request.headers.get("cookie") || "";
  for (const part of cookie.split(";")) {
    const [key, ...rest] = part.trim().split("=");
    if (key === name) return decodeURIComponent(rest.join("="));
  }
  return null;
}

function buildSessionCookie(sessionId, secure) {
  return "wol_session=" + encodeURIComponent(sessionId) +
    "; Path=/; HttpOnly; SameSite=Lax" +
    (secure ? "; Secure" : "") +
    "; Max-Age=2592000";
}

function randomToken(byteLength) {
  const bytes = new Uint8Array(byteLength);
  crypto.getRandomValues(bytes);
  let binary = "";
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary).replaceAll("+", "-").replaceAll("/", "_").replaceAll("=", "");
}

async function deriveEncryptionKey(secret) {
  const digest = await crypto.subtle.digest(
    "SHA-256",
    new TextEncoder().encode(secret)
  );
  return crypto.subtle.importKey("raw", digest, { name: "AES-GCM" }, false, ["encrypt", "decrypt"]);
}

async function encryptSecret(value, secret) {
  const key = await deriveEncryptionKey(secret);
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const ciphertext = new Uint8Array(
    await crypto.subtle.encrypt(
      { name: "AES-GCM", iv },
      key,
      new TextEncoder().encode(value)
    )
  );
  const combined = new Uint8Array(iv.length + ciphertext.length);
  combined.set(iv, 0);
  combined.set(ciphertext, iv.length);
  return bytesToBase64Url(combined);
}

async function decryptSecret(encoded, secret) {
  const combined = base64UrlToBytes(encoded);
  if (combined.length <= 12) throw new Error("Invalid encrypted payload");
  const iv = combined.slice(0, 12);
  const ciphertext = combined.slice(12);
  const key = await deriveEncryptionKey(secret);
  const plaintext = await crypto.subtle.decrypt(
    { name: "AES-GCM", iv },
    key,
    ciphertext
  );
  return new TextDecoder().decode(plaintext);
}

function bytesToBase64Url(bytes) {
  let binary = "";
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary).replaceAll("+", "-").replaceAll("/", "_").replaceAll("=", "");
}

function base64UrlToBytes(value) {
  const padded = value.replaceAll("-", "+").replaceAll("_", "/") + "===".slice((value.length + 3) % 4);
  const binary = atob(padded);
  return Uint8Array.from(binary, (char) => char.charCodeAt(0));
}

function validatePlan(payload) {
  const errors = [];

  if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
    return { ok: false, errors: ["body must be an object"] };
  }

  if (typeof payload.title !== "string" || !payload.title.trim()) {
    errors.push("title is required");
  } else if (payload.title.trim().length > 160) {
    errors.push("title is too long");
  }

  if (
    payload.description !== undefined &&
    payload.description !== null &&
    typeof payload.description !== "string"
  ) {
    errors.push("description must be a string");
  }

  if (!Array.isArray(payload.items) || payload.items.length === 0) {
    errors.push("items must contain at least one workout");
  } else if (payload.items.length > 7) {
    errors.push("PoC 1 supports at most 7 plan items");
  } else {
    const itemIds = new Set();

    payload.items.forEach((item, index) => {
      if (!item || typeof item !== "object" || Array.isArray(item)) {
        errors.push("items[" + index + "] must be an object");
        return;
      }

      if (!Number.isInteger(item.day_offset) || item.day_offset < 0 || item.day_offset > 6) {
        errors.push("items[" + index + "].day_offset must be an integer from 0 to 6");
      }

      if (!item.workout || typeof item.workout !== "object" || Array.isArray(item.workout)) {
        errors.push("items[" + index + "].workout must be an object");
      }

      if (item.item_id !== undefined) {
        if (typeof item.item_id !== "string" || !item.item_id.trim()) {
          errors.push("items[" + index + "].item_id must be a non-empty string");
        } else if (itemIds.has(item.item_id)) {
          errors.push("items[" + index + "].item_id is duplicated");
        } else {
          itemIds.add(item.item_id);
        }
      }
    });
  }

  return { ok: errors.length === 0, errors };
}

function readBearerToken(request) {
  const value = request.headers.get("authorization") || "";
  const match = /^Bearer\s+(.+)$/i.exec(value);
  return match ? match[1] : null;
}

function safeEqual(a, b) {
  const encoder = new TextEncoder();
  const left = encoder.encode(a);
  const right = encoder.encode(b);

  if (left.length !== right.length) return false;

  let diff = 0;
  for (let i = 0; i < left.length; i += 1) {
    diff |= left[i] ^ right[i];
  }
  return diff === 0;
}

function randomPublicId() {
  const bytes = new Uint8Array(18);
  crypto.getRandomValues(bytes);
  let binary = "";
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary).replaceAll("+", "-").replaceAll("/", "_").replaceAll("=", "");
}

function normalizeOptionalText(value) {
  if (typeof value !== "string") return null;
  const normalized = value.trim();
  return normalized || null;
}

function workoutName(workout) {
  if (!workout || typeof workout !== "object") return "Workout";
  const candidates = [workout.name, workout.workoutName, workout.title];
  const name = candidates.find((value) => typeof value === "string" && value.trim());
  return name ? name.trim() : "Workout";
}

function dayName(offset) {
  return ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"][offset] || "Giorno";
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function renderPlanPage(plan, items, oauthConfigured) {
  const description = plan.description
    ? '<p class="description">' + escapeHtml(plan.description) + "</p>"
    : "";

  const workoutCards = items.map((item) =>
    '<article class="workout">' +
      '<div class="day">' + escapeHtml(dayName(item.day_offset)) + "</div>" +
      '<div class="name">' + escapeHtml(workoutName(item.workout)) + "</div>" +
    "</article>"
  ).join("");

  return pageShell(
    escapeHtml(plan.title),
    '<main class="card">' +
      '<div class="product-brand product-brand-link" aria-label="WORKOUT Link"><div class="brand-symbol link-symbol" aria-hidden="true"><span class="link-a"></span><span class="link-b"></span><span class="link-spark"></span></div><div class="brand-copy"><div class="brand-master">WORKOUT</div><div class="brand-product">Link</div><div class="brand-tagline">SHARE <b>•</b> SCHEDULE <b>•</b> DELIVER</div></div></div>' +
      "<h1>" + escapeHtml(plan.title) + "</h1>" +
      description +
      '<section class="workouts">' +
        (workoutCards || "<p>Nessun allenamento disponibile.</p>") +
      "</section>" +
      '<section class="delivery">' +
        (oauthConfigured
          ? '<form method="get" action="/oauth/intervals/start">' +
              '<input type="hidden" name="public_id" value="' + escapeHtml(plan.public_id) + '">' +
              '<label for="week-start">Settimana che inizia lunedì</label>' +
              '<input id="week-start" name="week_start" type="date" required>' +
              '<div class="buttons">' +
                '<button type="submit" name="destination" value="garmin">Garmin</button>' +
                '<button type="submit" name="destination" value="suunto">Suunto</button>' +
              '</div>' +
              '<p class="note">Al primo utilizzo verrai reindirizzato a Intervals.icu per autorizzare il calendario.</p>' +
            '</form>'
          : '<label for="week-start">Settimana che inizia lunedì</label>' +
            '<input id="week-start" type="date" disabled>' +
            '<div class="buttons"><button type="button" disabled>Garmin</button><button type="button" disabled>Suunto</button></div>' +
            '<p class="note">OAuth Intervals.icu in attesa di approvazione/configurazione.</p>') +
      "</section>" +
      "<details><summary>Configurazione iniziale</summary>" +
      "<p>Per target cardio configura le zone HR in Intervals.icu. Per target passo configura ritmo soglia e zone passo. Garmin/Suunto dovranno avere l'upload degli allenamenti pianificati attivo.</p>" +
      "</details>" +
    "</main>",
  );
}

function renderHome() {
  return pageShell(
    "WORKOUT Link",
    '<main class="card"><div class="product-brand product-brand-link" aria-label="WORKOUT Link"><div class="brand-symbol link-symbol" aria-hidden="true"><span class="link-a"></span><span class="link-b"></span><span class="link-spark"></span></div><div class="brand-copy"><div class="brand-master">WORKOUT</div><div class="brand-product">Link</div><div class="brand-tagline">SHARE <b>•</b> SCHEDULE <b>•</b> DELIVER</div></div></div><h1>Workouts, one link away.</h1><p>PoC single-publisher in costruzione.</p></main>',
  );
}

function renderSetupPending() {
  return pageShell(
    "OAuth non ancora disponibile - WORKOUT Link",
    '<main class="card"><div class="product-brand product-brand-link" aria-label="WORKOUT Link"><div class="brand-symbol link-symbol" aria-hidden="true"><span class="link-a"></span><span class="link-b"></span><span class="link-spark"></span></div><div class="brand-copy"><div class="brand-master">WORKOUT</div><div class="brand-product">Link</div><div class="brand-tagline">SHARE <b>•</b> SCHEDULE <b>•</b> DELIVER</div></div></div><h1>Connessione non ancora disponibile</h1>' +
    "<p>L'app OAuth Intervals.icu è ancora in fase di approvazione o non è stata configurata nel Worker.</p>" +
    "</main>",
  );
}

function renderOAuthError(error) {
  const message = error === "access_denied"
    ? "Autorizzazione annullata. Nessun allenamento è stato aggiunto."
    : "Non è stato possibile completare la connessione a Intervals.icu.";
  return pageShell(
    "OAuth error - WORKOUT Link",
    '<main class="card"><div class="product-brand product-brand-link" aria-label="WORKOUT Link"><div class="brand-symbol link-symbol" aria-hidden="true"><span class="link-a"></span><span class="link-b"></span><span class="link-spark"></span></div><div class="brand-copy"><div class="brand-master">WORKOUT</div><div class="brand-product">Link</div><div class="brand-tagline">SHARE <b>•</b> SCHEDULE <b>•</b> DELIVER</div></div></div><h1>Connessione Intervals.icu</h1><p>' +
    escapeHtml(message) +
    "</p></main>",
  );
}

function renderPrivacy() {
  return pageShell(
    "Privacy - WORKOUT Link",
    '<main class="card"><div class="product-brand product-brand-link" aria-label="WORKOUT Link"><div class="brand-symbol link-symbol" aria-hidden="true"><span class="link-a"></span><span class="link-b"></span><span class="link-spark"></span></div><div class="brand-copy"><div class="brand-master">WORKOUT</div><div class="brand-product">Link</div><div class="brand-tagline">SHARE <b>•</b> SCHEDULE <b>•</b> DELIVER</div></div></div><h1>Privacy</h1>' +
    "<p>WORKOUT Link conserva gli snapshot dei piani pubblicati necessari alla condivisione tramite link.</p>" +
    "<p>I token Intervals.icu sono gestiti lato server, cifrati prima della memorizzazione e non sono esposti nel link pubblico o nel browser. WORKOUT Link non richiede password Garmin o Suunto.</p>" +
    "</main>",
  );
}

function pageShell(title, body) {
  return '<!doctype html><html lang="it"><head><meta charset="utf-8">' +
    '<meta name="viewport" content="width=device-width,initial-scale=1">' +
    "<title>" + title + "</title>" +
    "<style>" +
    "*{box-sizing:border-box}" +
    ":root{font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;color:#18312B;background:#F6F8F7}" +
    "body{margin:0;background:#F6F8F7;color:#18312B}" +
    ".card{width:min(980px,calc(100% - 32px));margin:0 auto;padding:36px 0 56px}" +
    " .product-brand{display:flex;align-items:flex-end;gap:14px;margin-bottom:26px}.brand-copy{display:grid;line-height:.9}.brand-master{font-size:clamp(34px,5vw,58px);font-weight:950;letter-spacing:-.055em;color:#0A4A42}.brand-product{margin-top:5px;font-size:clamp(25px,3.5vw,42px);font-weight:750;letter-spacing:-.04em;color:#F2B323}.brand-tagline{margin-top:14px;font-size:10px;font-weight:800;letter-spacing:.2em;color:#60736E}.brand-tagline b{color:#F2B323}.brand-symbol{flex:0 0 auto}.link-symbol{position:relative;width:66px;height:58px}.link-a,.link-b{position:absolute;width:34px;height:18px;border:8px solid;border-radius:14px;transform:rotate(-38deg)}.link-a{left:2px;bottom:6px;border-color:#0A4A42}.link-b{left:24px;top:4px;border-color:#F2B323}.link-spark{position:absolute;right:0;top:5px;width:7px;height:22px;background:#F2B323;border-radius:8px;transform:rotate(38deg)}" +
    "h1{margin:18px 0 8px;font-size:clamp(2.2rem,6vw,4.4rem);line-height:.98;color:#173C35}" +
    ".description,.note{color:#697386}" +
    ".workouts{display:grid;gap:12px;margin:30px 0}" +
    ".workout{border:1px solid #D7E2DF;border-left:5px solid #00796B;border-radius:16px;padding:16px 18px;background:#fff;box-shadow:0 5px 18px rgba(29,44,72,.04)}" +
    ".workout:nth-child(3n+1){border-left-color:#FBC02D}.workout:nth-child(3n+2){border-left-color:#FF5722}.workout:nth-child(3n+3){border-left-color:#00796B}" +
    ".day{font-size:.78rem;font-weight:800;text-transform:uppercase;color:#60736E;letter-spacing:.04em}" +
    ".name{font-size:1.15rem;font-weight:800;margin-top:5px;color:#173C35}" +
    ".delivery{margin-top:26px;padding:24px;border:1px solid #D7E2DF;border-radius:16px;background:#fff;box-shadow:0 5px 18px rgba(29,44,72,.04)}" +
    "label{display:block;font-weight:800;margin-bottom:9px;color:#465853}" +
    "input,button{font:inherit;padding:12px 14px;border-radius:10px;border:1px solid #C8D6D2}" +
    "input{width:min(320px,100%);background:#fff;color:#18312B}" +
    "input:focus{outline:3px solid rgba(0,121,107,.14);border-color:#00796B}" +
    ".buttons{display:flex;gap:10px;margin-top:14px;flex-wrap:wrap}" +
    "button{min-width:128px;font-weight:800;cursor:pointer;background:#fff;color:#00796B;border-color:#00796B}" +
    "button:hover:not(:disabled){background:#EAF4F2}" +
    "button:disabled{opacity:.45;cursor:not-allowed}" +
    "details{margin-top:22px;padding:18px 20px;border:1px solid #D7E2DF;border-radius:14px;background:#fff}" +
    "summary{cursor:pointer;font-weight:800;color:#173C35}" +
    "details p{color:#61736F;line-height:1.55}" +
    "@media (max-width:620px){.card{width:min(100% - 20px,980px);padding-top:20px}.delivery{padding:18px}.buttons{flex-direction:column}.buttons button{width:100%}.product-brand{align-items:center}.link-symbol{width:52px;height:46px}.link-a,.link-b{width:28px;height:15px;border-width:7px}.brand-tagline{font-size:9px;letter-spacing:.12em}}" +
    "</style></head><body>" +
    body +
    "</body></html>";
}

function jsonResponse(data, status = 200) {
  return new Response(JSON.stringify(data), { status, headers: JSON_HEADERS });
}

function htmlResponse(html, status = 200) {
  return new Response(html, { status, headers: HTML_HEADERS });
}
