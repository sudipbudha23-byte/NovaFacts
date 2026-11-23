/* NovaFacts Global Loading Controller */
(function(){
  var started=Date.now();
  function hideLoader(){
    var loader=document.getElementById("nf-global-loader");
    if(!loader)return;
    var wait=Math.max(0,1350-(Date.now()-started));
    window.setTimeout(function(){
      loader.classList.add("nf-hidden");
      document.body.classList.remove("nf-is-loading");
      window.setTimeout(function(){if(loader.parentNode)loader.parentNode.removeChild(loader)},350);
    },wait);
  }
  if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",hideLoader,{once:true});
  else hideLoader();
  window.addEventListener("pageshow",function(){var el=document.getElementById("nf-global-loader");if(el){el.classList.add("nf-hidden");document.body.classList.remove("nf-is-loading")}}, {once:true});
})();
