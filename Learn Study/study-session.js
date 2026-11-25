(()=> {
  const API_URL = "https://script.google.com/macros/s/AKfycbzfEr5e5Timz36UPwrAEAMu32LJ_-M5QjOf13mFtmTMJPSQxSJKCypYmeDhXVR2dNlM3g/exec";
  const TOKEN_KEY = "novafacts_study_token";
  const USER_KEY = "novafacts_study_user";

  async function callApi(action, data = {}) {
    const response = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "text/plain;charset=utf-8" },
      body: JSON.stringify({ action, ...data })
    });
    if (!response.ok) throw new Error("Authentication service unavailable");
    return response.json();
  }

  async function protectPage() {
    const token = sessionStorage.getItem(TOKEN_KEY);
    if (!token) return redirectToLogin();
    try {
      const result = await callApi("verify", { token });
      if (!result.ok) {
        sessionStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem(USER_KEY);
        return redirectToLogin();
      }
      localStorage.setItem(USER_KEY, JSON.stringify(result.user));
      document.documentElement.classList.add("nf-study-session");
      const name = document.getElementById("studyUserName");
      if (name && result.user && result.user.name) name.textContent = result.user.name;
      window.novaFactsStudyLogout = async function () {
        try { await callApi("logout", { token }); } catch (error) { /* clear local session regardless */ }
        sessionStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem(USER_KEY);
        location.replace("register.html");
      };
    } catch (error) {
      // Fail closed: do not show the protected dashboard if server verification fails.
      sessionStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(USER_KEY);
      redirectToLogin("session_check_failed");
    }
  }

  function redirectToLogin(reason) {
    const next = location.pathname + location.search + location.hash;
    location.replace("register.html?next=" + encodeURIComponent(next) + (reason ? "&reason=" + reason : ""));
  }

  protectPage();
})();