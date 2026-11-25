import{initializeApp}from"https://www.gstatic.com/firebasejs/13.1.0/firebase-app.js";
import{getAuth,onAuthStateChanged}from"https://www.gstatic.com/firebasejs/13.1.0/firebase-auth.js";
const firebaseConfig={apiKey:"AIzaSyAhIvLbAsi7M-TOTBix5q8ihoJ64M_1QU0",authDomain:"lcci-6c2a3.firebaseapp.com",projectId:"lcci-6c2a3",storageBucket:"lcci-6c2a3.firebasestorage.app",messagingSenderId:"486309279972",appId:"1:486309279972:web:bac73946ce8993a41194f1"};
const auth=getAuth(initializeApp(firebaseConfig));
const next=location.pathname+location.search+location.hash;
onAuthStateChanged(auth,user=>{
 if(!user){location.replace("/login.html?next="+encodeURIComponent(next)+"&source=study");return;}
 document.documentElement.classList.add("nf-study-authorized");
});
