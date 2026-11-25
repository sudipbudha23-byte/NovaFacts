(() => {
  "use strict";
  const TOKEN_KEY = "novafacts_study_token";
  const SESSION_KEY = "novafacts_study_logged_in";
  const USER_KEY = "novafacts_study_user";
  const token = localStorage.getItem(TOKEN_KEY);
  const redirectToLogin = () => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(SESSION_KEY);
    localStorage.removeItem(USER_KEY);
    const next = location.pathname + location.search + location.hash;
    location.replace("/Learn%20Study/register.html?next=" + encodeURIComponent(next));
  };

  if (!token) {
    redirectToLogin();
    return;
  }

  document.documentElement.classList.add("nf-study-session-checking");
  fetch("/api/study-auth", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    cache: "no-store",
    body: JSON.stringify({ action: "verify", token })
  })
    .then(response => response.json())
    .then(result => {
      if (!result || !result.ok || !result.user) {
        redirectToLogin();
        return;
      }
      localStorage.setItem(SESSION_KEY, "true");
      localStorage.setItem(USER_KEY, JSON.stringify(result.user));
      document.documentElement.classList.remove("nf-study-session-checking");
      document.documentElement.classList.add("nf-study-session");
    })
    .catch(redirectToLogin);
})();
