// The one line of desktop/preload.cjs that tells the interface it runs in the desktop window (nothing else of it).
window.addEventListener('DOMContentLoaded', () => { if (process.platform === 'win32') document.documentElement.classList.add('desktop-integrated-titlebar'); });
