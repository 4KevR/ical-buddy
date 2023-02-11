/*!
 * Color mode toggler for Bootstrap's docs (https://getbootstrap.com/)
 * Copyright 2011-2022 The Bootstrap Authors
 * Licensed under the Creative Commons Attribution 3.0 Unported License.
 */

(() => {
    'use strict'

    const storedTheme = localStorage.getItem('theme')

    const getPreferredTheme = () => {
        if (storedTheme) {
            return storedTheme
        }

        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
    }

    const setTheme = function (theme) {
        if (theme === 'auto' && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            document.documentElement.setAttribute('data-bs-theme', 'dark')
        } else {
            document.documentElement.setAttribute('data-bs-theme', theme)
        }
    }

    setTheme(getPreferredTheme())

    const showActiveTheme = theme => {
        if (theme === 'auto' && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            document.querySelector('#lordIcon').setAttribute('colors', 'primary:#b4b4b4');
            document.querySelector('#githubIcon').style.color = '#b4b4b4';
        } else {
            document.querySelector('#lordIcon').setAttribute('colors', theme === 'dark' ? 'primary:#b4b4b4' : 'primary:#000000');
            document.querySelector('#githubIcon').style.color = theme === 'dark' ? '#b4b4b4' : '#000000';
        }

        const activeThemeIcon = document.querySelector('.theme-icon-active use')
        const btnToActive = document.querySelector(`[data-bs-theme-value="${theme}"]`)

        document.querySelectorAll('[data-bs-theme-value]').forEach(element => {
            element.classList.remove('active')
        })

        btnToActive.classList.add('active')
    }

    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
        if (storedTheme !== 'light' || storedTheme !== 'dark') {
            setTheme(getPreferredTheme())
        }
    })

    window.addEventListener('DOMContentLoaded', () => {
        showActiveTheme(getPreferredTheme())

        document.querySelectorAll('[data-bs-theme-value]')
            .forEach(toggle => {
                toggle.addEventListener('click', () => {
                    const theme = toggle.getAttribute('data-bs-theme-value')
                    localStorage.setItem('theme', theme)
                    setTheme(theme)
                    showActiveTheme(theme)
                })
            })
    })
})()

// Custom functions
function addValidityListenerOnce(element) {
    element.reportValidity();
    element.addEventListener("input", function () {
        element.setCustomValidity("");
    }, {once: true});
}

function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}

async function sendRequest(url, body) {
    const options = {
        method: 'post',
        credentials: 'same-origin',
        headers: {
            'X-CSRF-TOKEN': getCookie('csrf_access_token'),
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
    };
    return await fetch(url, options);
}

document.addEventListener('DOMContentLoaded', () => {
    if (["/", "/account"].includes(location.pathname)) {
        const navElement = document.querySelector('a.nav-link[href="' + location.pathname + '"]');
        navElement.classList.add('active');
        navElement.setAttribute('aria-current', 'page');
    }
});