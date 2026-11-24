(() => {
  "use strict";
  const ads = [
    { image: "https://static.hilltopads.com/other/banners/pub/make_big_money/728x90.gif?v=1795373373", click: "https://plump-plastic.com/7JdpH1", alt: "HilltopAds advertisement" },
    { image: "https://static.hilltopads.com/other/banners/adv/ht_advantages/728x90.gif?v=1795373373", click: "https://plump-plastic.com/7JdpH1", alt: "HilltopAds advantages advertisement" },
    { image: "https://static.hilltopads.com/other/banners/adv/boost_roi/728x90.gif?v=1795373373", click: "https://plump-plastic.com/7JdpH1", alt: "HilltopAds boost ROI advertisement" }];
  let counter = 0;
  const isExternal = url => /^https:\/\//i.test(url);
  function creative(item) {
    if (item.direct) {
      const a = document.createElement("a");
      a.className = "nf-ad-direct";
      a.href = item.click;
      a.target = "_blank";
      a.rel = "nofollow sponsored noopener noreferrer";
      a.innerHTML = '<span><strong></strong><span></span></span><b>खोल्नुहोस् ↗</b>';
      a.querySelector("strong").textContent = item.title;
      a.querySelector("span span").textContent = item.description;
      return a;
    }
    const a = document.createElement("a");
    a.className = "nf-ad-link";
    a.href = item.click;
    a.target = "_blank";
    a.rel = "nofollow sponsored noopener noreferrer";
    const img = document.createElement("img");
    img.src = item.image;
    img.alt = item.alt;
    img.width = 728;
    img.height = 90;
    img.loading = "lazy";
    img.decoding = "async";
    a.appendChild(img);
    return a;
  }
  function slot(kind, rotate) {
    const wrap = document.createElement("aside");
    wrap.className = "nf-ad-slot nf-ad-slot--" + kind;
    wrap.setAttribute("aria-label", "Advertisement");
    const label = document.createElement("span");
    label.className = "nf-ad-label";
    label.textContent = "ADVERTISEMENT";
    const content = document.createElement("div");
    content.className = "nf-ad-content";
    wrap.append(label, content);
    let index = counter++ % ads.length;
    const render = () => {
      content.replaceChildren(creative(ads[index]));
      index = (index + 1) % ads.length;
    };
    render();
    if (rotate) window.setInterval(render, 18000);
    return wrap;
  }
  function rail() {
    const wrap = document.createElement("aside");
    wrap.className = "nf-ad-rail-fixed";
    wrap.setAttribute("aria-label", "Vertical advertisement column");
    const title = document.createElement("span");
    title.className = "nf-ad-label";
    title.textContent = "ADVERTISEMENT";
    wrap.appendChild(title);
    ads.forEach(item => {
      const unit = document.createElement("div");
      unit.className = "nf-ad-slot";
      unit.appendChild(creative(item));
      wrap.appendChild(unit);
    });
    return wrap;
  }
  function after(node, target) { if (node && target && target.parentNode) target.parentNode.insertBefore(node, target.nextSibling); }
  function before(node, target) { if (node && target && target.parentNode) target.parentNode.insertBefore(node, target); }
  function addRailToAside(aside) {
    if (aside) aside.insertBefore(slot("rail", true), aside.firstChild);
    else document.body.appendChild(rail());
  }
  function init() {
    const path = location.pathname.toLowerCase();
    if (path.endsWith("/index.html") || path === "/" || path.endsWith("/")) {
      document.querySelectorAll(".hilltop-ad").forEach(el => el.remove());
      const welcome = document.querySelector(".welcome");
      const newsGrid = document.getElementById("newsGrid");
      const quiz = document.getElementById("quiz");
      after(slot("horizontal", true), welcome);
      after(slot("horizontal", true), newsGrid);
      before(slot("horizontal", true), quiz);
      addRailToAside(document.querySelector(".right-sidebar"));
    } else if (path.includes("gpacalculator")) {
      const hero = document.querySelector("main .hero");
      const result = document.getElementById("resultSection");
      after(slot("horizontal", true), hero);
      after(slot("horizontal", true), result);
      document.body.appendChild(rail());
    } else if (path.includes("black-holes")) {
      const main = document.querySelector("main");
      const definition = document.getElementById("definition");
      const quiz = document.getElementById("quiz");
      const sources = document.getElementById("sources");
      after(slot("horizontal", true), definition);
      before(slot("horizontal", true), quiz);
      before(slot("horizontal", true), sources);
      if (main) document.body.appendChild(rail());
    } else if (path.includes("news-detail")) {
      const details = document.getElementById("details");
      const source = document.querySelector(".source-box");
      const side = document.querySelector(".content-layout .sidebar");
      after(slot("horizontal", true), details);
      after(slot("horizontal", true), source);
      addRailToAside(side);
    } else if (path.includes("question-bank")) {
      const hero = document.querySelector("main .hero");
      const layout = document.querySelector("main .layout");
      const paper = document.getElementById("paper");
      after(slot("horizontal", true), hero);
      after(slot("horizontal", true), layout);
      before(slot("horizontal", true), paper);
      addRailToAside(document.querySelector(".layout aside"));
    }
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init, { once: true });
  else init();
})();