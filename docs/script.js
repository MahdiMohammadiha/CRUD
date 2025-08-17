const toggleButton = document.getElementById('toggle-theme');
const root = document.documentElement;
const savedTheme = localStorage.getItem('theme');

if (savedTheme === 'dark') {
    root.classList.add('dark');
    toggleButton.textContent = '🌞';
}

toggleButton.addEventListener('click', () => {
    const isDark = root.classList.toggle('dark');
    toggleButton.textContent = isDark ? '🌞' : '🌙';
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
});

const copySVG = `
            <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                <rect width="24" height="24" fill="none" opacity="0"/>
                <g transform="matrix(1 0 0 1 12 12)">
                    <path transform="translate(-12, -12)" d="M4 2C2.895 2 2 2.895 2 4L2 18L4 18L4 4L18 4L18 2L4 2z M8 6C6.895 6 6 6.895 6 8L6 20C6 21.105 6.895 22 8 22L20 22C21.105 22 22 21.105 22 20L22 8C22 6.895 21.105 6 20 6L8 6z M8 8L20 8L20 20L8 20L8 8z" fill="currentColor"/>
                </g>
            </svg>
        `;

const tickSVG = `
            <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                <rect width="24" height="24" fill="none" opacity="0"/>
                <g transform="matrix(1 0 0 1 12 12)">
                    <path transform="translate(-12, -12)" d="M5 2C3.3545455 2 2 3.3545455 2 5L2 19C2 20.645455 3.3545455 22 5 22L19 22C20.645455 22 22 20.645455 22 19L22 11L20 11L20 19C20 19.554545 19.554545 20 19 20L5 20C4.4454545 20 4 19.554545 4 19L4 5C4 4.4454545 4.4454545 4 5 4L14 4L14 2L5 2z M20.472656 3.9140625L11.179688 13.765625L7.5078125 10.09375L6.09375 11.507812L11.220703 16.634766L21.927734 5.2871094L20.472656 3.9140625z" fill="currentColor"/>
                </g>
            </svg>
        `;

function createCopyButton() {
    const btn = document.createElement('button');
    btn.className = 'copy-btn';
    btn.title = 'Copy to clipboard';
    btn.innerHTML = copySVG;
    return btn;
}

document.querySelectorAll('.code-block').forEach(pre => {
    const btn = createCopyButton();
    pre.appendChild(btn);
});

document.querySelectorAll('.copy-btn').forEach(button => {
    button.addEventListener('click', () => {
        const code = button.parentElement.querySelector('code');
        if (!code) return;

        navigator.clipboard.writeText(code.innerText).then(() => {
            button.innerHTML = tickSVG;
            setTimeout(() => {
                button.innerHTML = copySVG;
            }, 2000);
        }).catch(err => console.error('Failed to copy text: ', err));
    });
});