(function(){
  if(window.__novaMobileNavLoaded)return;window.__novaMobileNavLoaded=true;
  var fullPath=decodeURIComponent(location.pathname).toLowerCase();
  var path=fullPath.split('/').pop()||'index.html';
  var base=fullPath.indexOf('/learn study/')>=0?'../':'';
  var items=[
    {label:'Home',icon:'🏠',href:'index.html',match:['','index.html']},
    {label:'Computer',icon:'💻',href:'Code%20Study.html',match:['code study.html','virtual-lab.html']},
    {label:'Study',icon:'📚',href:'Learn%20Study/index.html',match:['learn study/index.html','learn study/feature.html','learn study/science-lab.html','ai-learning.html','periodic table.html','g pacalculator.html','gpacalculator.html','question-bank.html'],center:true},
    {label:'Dashboard',icon:'📊',href:'dashboard.html',match:['dashboard.html']},
    {label:'Quiz',icon:'🧠',href:'quiz.html',match:['quiz.html']}
  ];
  var nav=document.createElement('nav');nav.id='nf-mobile-nav';nav.setAttribute('aria-label','Mobile navigation');
  items.forEach(function(item){
    var a=document.createElement('a');a.href=base+item.href;a.className=(item.center?'nf-study ':'')+(item.label==='Dashboard'?'nf-dashboard ':'')+(item.match.indexOf(path)>=0?'nf-active':'');
    if(item.match.indexOf(path)>=0 || (item.label==='Study' && fullPath.indexOf('/learn study/')>=0)){a.classList.add('nf-active');a.setAttribute('aria-current','page');}
    var icon=document.createElement('span');icon.className='nf-nav-icon';icon.textContent=item.icon;
    var label=document.createElement('span');label.className='nf-nav-label';label.textContent=item.label;
    a.appendChild(icon);a.appendChild(label);nav.appendChild(a);
  });
  document.body.appendChild(nav);
})();