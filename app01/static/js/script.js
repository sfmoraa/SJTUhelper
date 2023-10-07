let loginForm = document.querySelector('.login-form');

document.querySelector('#login-btn').onclick = () =>{
   loginForm.classList.add('active');
}

document.querySelector('#close-login-form').onclick = () =>{
   loginForm.classList.remove('active');
}

let menu = document.querySelector('#menu-btn');
let navbar = document.querySelector('.header .nav');

menu.onclick = () =>{
   menu.classList.toggle('fa-times');
   navbar.classList.toggle('active');
}

window.onscroll = () =>{
   loginForm.classList.remove('active');
   menu.classList.remove('fa-times');
   navbar.classList.remove('active');

   if(window.scrollY > 0){
      document.querySelector('.header').classList.add('active');
   }else{
      document.querySelector('.header').classList.remove('active');
   }
}

function ListAnimation(){
	const boxes = document.querySelectorAll('.blog-slider')
    window.addEventListener('scroll', checkBoxes,true)
    checkBoxes();
    function checkBoxes() {
      const triggerBottom = window.innerHeight / 5 * 4
      boxes.forEach(box => {
        const boxTop = box.getBoundingClientRect().top
        if (boxTop < triggerBottom) {
          box.classList.add('show')
        } else {
          box.classList.remove('show')
        }
      })
    }
}
