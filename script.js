const signUpButton = document.getElementById('signUp');
const signInButton = document.getElementById('signIn');
const container = document.getElementById('container');

signUpButton.addEventListener('click', () => {
	container.classList.add("right-panel-active");
});

signInButton.addEventListener('click', () => {
	if (window.signInSignedIn && typeof window.logoutSession === 'function') {
		window.logoutSession();
		return;
	}
	container.classList.remove("right-panel-active");
});
