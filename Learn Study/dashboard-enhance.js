(()=>{'use strict';
const root=document.documentElement,body=document.body;
const css=`
:root[data-theme="light"]{--ink:#17263b;--muted:#66758a;--blue:#176f9f;--blue2:#eaf4fb;--line:#e1e8f0;--bg:#f4f7fb;--white:#fff;--green:#15966e}
:root[data-theme="light"] body{background:radial-gradient(ellipse at 75% -15%,#e5f1ff 0,transparent 42%),#f4f7fb;color:#17263b}
:root[data-theme="light"] .sidebar{background:rgba(255,255,255,.96);border-color:#e1e8f0}
:root[data-theme="light"] .logo{color:#176b9d}:root[data-theme="light"] .logo span{color:#263f56}
:root[data-theme="light"] .student-profile{background:linear-gradient(145deg,#f3faff,#fff);border-color:#dcebf4}
:root[data-theme="light"] .student-identity strong{color:#18334b}:root[data-theme="light"] .student-identity span{color:#72869a}
:root[data-theme="light"] .nav a{color:#52677a}:root[data-theme="light"] .nav a:hover,:root[data-theme="light"] .nav a.active{background:#e5f4fc;color:#126d9f}
:root[data-theme="light"] .top h1{color:#18334b}:root[data-theme="light"] .profile{color:#4e6478}
:root[data-theme="light"] .game-hub{background:linear-gradient(145deg,#fff,#edf5fc);border-color:#dce9f2;box-shadow:0 12px 35px #1a547511}
:root[data-theme="light"] .game-welcome h2{color:#18334b}:root[data-theme="light"] .game-welcome p{color:#71869a}
:root[data-theme="light"] .game-stat,:root[data-theme="light"] .game-card{background:#fff;border-color:#e2edf4}
:root[data-theme="light"] .game-stat>span{color:#6e8294}:root[data-theme="light"] .game-stat strong{color:#18334b}:root[data-theme="light"] .game-stat small{color:#7c8fa0}
:root[data-theme="light"] .game-card h3{color:#18334b}:root[data-theme="light"] .game-card p{color:#74889a}
:root[data-theme="light"] .rank-card{background:linear-gradient(135deg,#18334b,#245b79);border-color:#58627a}
:root[data-theme="light"] .rank-card h3{color:#fff}:root[data-theme="light"] .rank-card p,:root[data-theme="light"] .rank-card small{color:#d2e5ef}
:root[data-theme="light"] .subject-grid a,:root[data-theme="light"] .activity-grid>div,:root[data-theme="light"] .recent-row{background:#f6fafc;border-color:#e5edf2}
:root[data-theme="light"] .subject-grid span,:root[data-theme="light"] .recent-copy strong{color:#29465d}
:root[data-theme="light"] .subject-grid small,:root[data-theme="light"] .recent-copy small{color:#8395a3}
:root[data-theme="light"] .activity-grid strong{color:#1a719c}
:root[data-theme="light"] .banner{background:linear-gradient(110deg,#176b9d,#2387b8);border-color:#d5e7f1}
:root[data-theme="light"] .panel,:root[data-theme="light"] .right-panel{background:#eaf6fc;border-color:#deeff8}
:root[data-theme="light"] .lesson,:root[data-theme="light"] .exam,:root[data-theme="light"] .quick a{background:#fff;border-color:#edf2f5;color:#18334b}
:root[data-theme="light"] .lesson h3{color:#18334b}:root[data-theme="light"] .lesson p{color:#8192a1}
:root[data-theme="light"] .search{background:#fff;color:#18334b;border-color:#e2edf4}
:root[data-theme="light"] footer{color:#8b9ba9}
.nf-theme-toggle{display:inline-flex;align-items:center;gap:7px;border:1px solid #536176;background:#202b3b;color:#f3d58e;border-radius:999px;padding:8px 11px;font-size:11px;font-weight:800;cursor:pointer}
.nf-theme-toggle:hover{transform:translateY(-1px);box-shadow:0 5px 16px #0002}
:root[data-theme="light"] .nf-theme-toggle{background:#fff;color:#34445a;border-color:#d7e1eb}
.nf-top-actions{display:flex;align-items:center;gap:12px}
@media(max-width:540px){.nf-top-actions{gap:7px}.nf-theme-toggle{padding:8px 9px;font-size:10px}.nf-theme-word{display:none}}
#nf-study-bottom-nav{display:none}
@media(max-width:760px){
#nf-study-bottom-nav{position:fixed;z-index:100000;left:10px;right:10px;bottom:calc(9px + env(safe-area-inset-bottom));height:76px;padding:5px 9px;display:grid;grid-template-columns:1fr 1fr 1.25fr 1fr 1fr;align-items:center;background:rgba(16,24,37,.94);border:1px solid #ffffff20;border-radius:25px;box-shadow:0 12px 35px #0006;backdrop-filter:blur(18px);-webkit-backdrop-filter:blur(18px)}
#nf-study-bottom-nav a{height:100%;min-width:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:4px;color:#aab7c9;text-decoration:none;font:700 10px/1.1 system-ui;position:relative;-webkit-tap-highlight-color:transparent}
#nf-study-bottom-nav .nf-bnav-icon{font-size:21px;line-height:1;transition:transform .2s}
#nf-study-bottom-nav a.nf-current{color:#f1cb79}
#nf-study-bottom-nav a.nf-center{height:100%;justify-content:flex-start}
#nf-study-bottom-nav a.nf-center .nf-bnav-icon{width:66px;height:66px;margin-top:-30px;display:grid;place-items:center;border:5px solid #0d1521;border-radius:50%;background:linear-gradient(145deg,#f3d58e,#bb8738);box-shadow:0 7px 22px #d6ad5860;color:#17202d;font-size:30px;transform:translateY(-1px)}
#nf-study-bottom-nav a.nf-center:active .nf-bnav-icon{transform:translateY(2px) scale(.94)}
#nf-study-bottom-nav a.nf-center .nf-bnav-label{margin-top:-1px;color:#f1cb79;font-weight:900}
body.nf-has-bottom-nav{padding-bottom:110px!important}
:root[data-theme="light"] #nf-study-bottom-nav{background:rgba(255,255,255,.95);border-color:#e1e8f0;box-shadow:0 12px 35px #29445a26}
:root[data-theme="light"] #nf-study-bottom-nav a{color:#718096}
:root[data-theme="light"] #nf-study-bottom-nav a.nf-current,:root[data-theme="light"] #nf-study-bottom-nav a.nf-center .nf-bnav-label{color:#176b9d}
:root[data-theme="light"] #nf-study-bottom-nav a.nf-center .nf-bnav-icon{border-color:#fff}
}
`;
const style=document.createElement('style');style.textContent=css;document.head.appendChild(style);
const actions=document.querySelector('.top .profile-menu-wrap');
if(actions&&!document.querySelector('.nf-theme-toggle')){
 const wrap=document.createElement('div');wrap.className='nf-top-actions';
 const btn=document.createElement('button');btn.type='button';btn.className='nf-theme-toggle';btn.innerHTML='<span class="nf-theme-icon">☀️</span><span class="nf-theme-word">Light mode</span>';
 wrap.appendChild(btn);actions.parentNode.insertBefore(wrap,actions);wrap.appendChild(actions);
 const apply=mode=>{root.setAttribute('data-theme',mode);btn.querySelector('.nf-theme-icon').textContent=mode==='dark'?'☀️':'🌙';btn.querySelector('.nf-theme-word').textContent=mode==='dark'?'Light mode':'Dark mode';btn.setAttribute('aria-label',mode==='dark'?'Switch to light theme':'Switch to dark theme')};
 let saved='dark';try{saved=localStorage.getItem('nf-study-theme')||'dark'}catch{}apply(saved);
 btn.addEventListener('click',()=>{const next=root.getAttribute('data-theme')==='dark'?'light':'dark';apply(next);try{localStorage.setItem('nf-study-theme',next)}catch{}});
}
const nav=document.createElement('nav');nav.id='nf-study-bottom-nav';nav.setAttribute('aria-label','Student navigation');
const items=[
 {label:'Home',icon:'⌂',href:'../index.html'},
 {label:'Dashboard',icon:'▦',href:'#dashboard'},
 {label:'Study',icon:'📚',href:'#lessons',center:true},
 {label:'Coaching',icon:'🎓',href:'feature.html'},
 {label:'Quiz',icon:'🧠',href:'../quiz.html'}
];
items.forEach(item=>{const a=document.createElement('a');a.href=item.href;if(item.center)a.className='nf-center';if(item.label==='Dashboard')a.classList.add('nf-current');const icon=document.createElement('span');icon.className='nf-bnav-icon';icon.textContent=item.icon;const label=document.createElement('span');label.className='nf-bnav-label';label.textContent=item.label;a.append(icon,label);nav.appendChild(a)});
body.appendChild(nav);body.classList.add('nf-has-bottom-nav');
})();