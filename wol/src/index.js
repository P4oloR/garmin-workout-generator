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
      return showPublicPlan(decodeURIComponent(url.pathname.slice(3)), env);
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

async function showPublicPlan(publicId, env) {
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

  return htmlResponse(renderPlanPage(plan, items));
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

function renderPlanPage(plan, items) {
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
      '<div class="brand">WorkOutLink</div>' +
      "<h1>" + escapeHtml(plan.title) + "</h1>" +
      description +
      '<section class="workouts">' +
        (workoutCards || "<p>Nessun allenamento disponibile.</p>") +
      "</section>" +
      '<section class="delivery">' +
        '<label for="week-start">Settimana che inizia lunedì</label>' +
        '<input id="week-start" type="date" disabled>' +
        '<div class="buttons"><button type="button" disabled>Garmin</button><button type="button" disabled>Suunto</button></div>' +
        '<p class="note">Delivery OAuth in arrivo nel prossimo step del PoC. Il piano pubblico è già consultabile.</p>' +
      "</section>" +
      "<details><summary>Configurazione iniziale</summary>" +
      "<p>Per target cardio configura le zone HR in Intervals.icu. Per target passo configura ritmo soglia e zone passo. Garmin/Suunto dovranno avere l'upload degli allenamenti pianificati attivo.</p>" +
      "</details>" +
    "</main>",
  );
}

function renderHome() {
  return pageShell(
    "WorkOutLink",
    '<main class="card"><div class="brand">WorkOutLink</div><h1>Workouts, one link away.</h1><p>PoC single-publisher in costruzione.</p></main>',
  );
}

function renderPrivacy() {
  return pageShell(
    "Privacy - WorkOutLink",
    '<main class="card"><div class="brand">WorkOutLink</div><h1>Privacy</h1>' +
    "<p>WorkOutLink conserva gli snapshot dei piani pubblicati necessari alla condivisione tramite link.</p>" +
    "<p>Nel prossimo step OAuth, i token Intervals.icu saranno gestiti lato server e non saranno esposti nel link pubblico o nel browser. WorkOutLink non richiede password Garmin o Suunto.</p>" +
    "</main>",
  );
}

function pageShell(title, body) {
  return '<!doctype html><html lang="it"><head><meta charset="utf-8">' +
    '<meta name="viewport" content="width=device-width,initial-scale=1">' +
    "<title>" + title + "</title>" +
    "<style>:root{font-family:system-ui,sans-serif;color-scheme:light dark}body{margin:0;padding:24px;background:Canvas;color:CanvasText}.card{max-width:720px;margin:0 auto}.brand{font-weight:800;letter-spacing:.04em;opacity:.75}h1{margin:10px 0 8px;font-size:clamp(2rem,6vw,3.5rem);line-height:1}.description,.note{opacity:.75}.workouts{display:grid;gap:10px;margin:28px 0}.workout{border:1px solid color-mix(in srgb,CanvasText 22%,transparent);border-radius:14px;padding:14px 16px}.day{font-size:.8rem;font-weight:700;text-transform:uppercase;opacity:.65}.name{font-size:1.1rem;font-weight:700;margin-top:4px}.delivery{border-top:1px solid color-mix(in srgb,CanvasText 20%,transparent);padding-top:22px}label{display:block;font-weight:700;margin-bottom:8px}input,button{font:inherit;padding:12px;border-radius:10px;border:1px solid color-mix(in srgb,CanvasText 25%,transparent)}input{width:min(280px,100%);box-sizing:border-box}.buttons{display:flex;gap:10px;margin-top:14px}button{min-width:120px;font-weight:800}details{margin-top:26px}summary{cursor:pointer;font-weight:700}</style></head><body>" +
    body +
    "</body></html>";
}

function jsonResponse(data, status = 200) {
  return new Response(JSON.stringify(data), { status, headers: JSON_HEADERS });
}

function htmlResponse(html, status = 200) {
  return new Response(html, { status, headers: HTML_HEADERS });
}
