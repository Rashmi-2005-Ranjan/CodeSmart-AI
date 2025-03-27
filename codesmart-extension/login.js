// login.js
let isLoginMode = true;

document.getElementById('authForm').addEventListener('submit', (event) => {
    event.preventDefault();

    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const username = document.getElementById('username').value;
    const authMessage = document.getElementById('auth_message');

    authMessage.textContent = isLoginMode ? 'Logging in...' : 'Registering...';

    // Retrieve stored users from chrome.storage.local
    chrome.storage.local.get('users', (data) => {
        let users = data.users || {};

        if (isLoginMode) {
            // Login
            if (users[email] && users[email].password === password) {
                // Successful login
                const user = { email, username: users[email].username };
                chrome.storage.local.set({ user }, () => {
                    chrome.runtime.sendMessage({ action: 'setPopup', popup: 'popup.html' }, () => {
                        window.location.href = 'popup.html';
                    });
                });
            } else {
                authMessage.textContent = 'Error: Invalid email or password';
            }
        } else {
            // Register
            if (!username.trim()) {
                authMessage.textContent = 'Error: Username is required for registration';
                return;
            }
            if (users[email]) {
                authMessage.textContent = 'Error: Email already registered';
                return;
            }

            // Store new user
            users[email] = { password, username };
            chrome.storage.local.set({ users }, () => {
                const user = { email, username };
                chrome.storage.local.set({ user }, () => {
                    chrome.runtime.sendMessage({ action: 'setPopup', popup: 'popup.html' }, () => {
                        window.location.href = 'popup.html';
                    });
                });
            });
        }
    });
});

document.getElementById('toggle_link').addEventListener('click', (event) => {
    event.preventDefault();
    isLoginMode = !isLoginMode;
    document.getElementById('auth_title').textContent = isLoginMode ? 'Login' : 'Register';
    document.getElementById('auth_button').textContent = isLoginMode ? 'Login' : 'Register';
    document.getElementById('toggle_auth').innerHTML = isLoginMode
        ? `Don't have an account? <a href="#" id="toggle_link">Register</a>`
        : `Already have an account? <a href="#" id="toggle_link">Login</a>`;
    document.getElementById('username_group').style.display = isLoginMode ? 'none' : 'block';
    document.getElementById('username').required = !isLoginMode;
    document.getElementById('auth_message').textContent = '';
});

// Check if user is already logged in
chrome.storage.local.get('user', (data) => {
    if (data.user) {
        chrome.runtime.sendMessage({ action: 'setPopup', popup: 'popup.html' }, () => {
            window.location.href = 'popup.html';
        });
    }
});


document.addEventListener("DOMContentLoaded", function () {
    document.getElementById("explore").addEventListener("click", function() {
        window.open("https://rashmi-2005-ranjan.github.io/Deploy/", "_blank");
    });
});