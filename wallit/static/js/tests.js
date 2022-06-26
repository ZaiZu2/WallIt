const logoColor = function(color, size) {
    const logo = document.querySelector('.logo');

    logo.style.color = color;

    logo.setAttribute('align-self', 'top')

    //logo.style.cssText = `color: green; font-size:${size}px`
}

const replaceLogo = function(imageSource) {

    const window = document.querySelector('.window');
    const menu = document.querySelector('.menu');
    const logo = document.querySelector('.logo');

    const img = document.createElement('div');
    img.style.backgroundColor = 'red';
    img.textContent = 'Replacement';

    window.removeChild(logo);
    window.insertBefore(img, menu);
}

const addStuff = function(){

    const div = document.createElement('div');
    div.style.cssText = 'border: 2px solid black; background-color: pink';

    const h1 = document.createElement('h1');
    h1.style.backgroundColor = 'black';
    h1.textContent = 'I AM H1.';

    const p1 = document.createElement('p');
    p1.textContent = "Hey, I'm Red";
    p1.style.color = 'Red';

    const p2 = document.createElement('p');
    p2.textContent = 'IM AM P2.'

    div.append(h1, p1, p2);

    const window = document.querySelector('.window');
    window.append(div);
}

/*
const btn = document.querySelector('#btn2');
btn.addEventListener('click', function(e) {
    console.log(e.target.style.backgroundColor = 'blue');
});*/

// buttons is a node list. It looks and acts much like an array.
const buttons = document.querySelectorAll('button');
buttons.forEach((button) => {
  button.addEventListener('keydown', () => {
    alert(button.id);
  });
});
