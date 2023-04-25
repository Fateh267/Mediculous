// Show/hide sign up form
document.querySelector('.signup-link a').addEventListener('click', function () {
    document.getElementById('login-form').style.display = 'none';
    document.getElementById('signup-form').style.display = 'block';
});

document.querySelector('.signup-link a[href="#login-form"]').addEventListener('click', function () {
    document.getElementById('login
