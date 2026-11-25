const GAS_URL = "https://script.google.com/macros/s/AKfycbzfEr5e5Timz36UPwrAEAMu32LJ_-M5QjOf13mFtmTMJPSQxSJKCypYmeDhXVR2dNlM3g/exec";

export async function onRequestPost({ request }) {
  let body;
  try { body = await request.json(); }
  catch { return Response.json({ ok: false, error: "Invalid JSON request." }, { status: 400 }); }

  const action = String(body?.action || "").toLowerCase();
  if (!["register", "login", "verify", "logout"].includes(action)) {
    return Response.json({ ok: false, error: "Unsupported action." }, { status: 400 });
  }
  if (JSON.stringify(body).length > 12000) {
    return Response.json({ ok: false, error: "Request is too large." }, { status: 413 });
  }

  try {
    const upstream = await fetch(GAS_URL, {
      method: "POST",
      headers: { "Content-Type": "text/plain;charset=UTF-8" },
      body: JSON.stringify(body),
      redirect: "follow"
    });
    const raw = await upstream.text();
    let data;
    try { data = JSON.parse(raw); }
    catch {
      return Response.json({ ok: false, error: "Authentication server returned an unreadable response." }, { status: 502 });
    }
    return Response.json(data, {
      headers: { "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff" }
    });
  } catch {
    return Response.json({ ok: false, error: "Could not connect to the authentication server. Please try again." }, { status: 502 });
  }
}
