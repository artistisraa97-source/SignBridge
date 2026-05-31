// Shared navbar auth handler for all pages
(function() {
	const AUTH_TOKEN_KEY = 'auth_token';
	const USER_EMAIL_KEY = 'user_email';

	function isUserSignedIn() {
		if (window.SB && window.SB.authToken !== null) return !!window.SB.authToken;
		const token = localStorage.getItem(AUTH_TOKEN_KEY);
		if (window.SB) window.SB.authToken = token || null;
		return !!token;
	}

	function findAuthNavLink() {
		const navMenu = document.querySelector('#navmenu ul');
		if (!navMenu) return null;

		const anchors = Array.from(navMenu.querySelectorAll('a'));
		return anchors.find(a => {
			const href = (a.getAttribute('href') || '').trim();
			const text = a.textContent.trim();
			return href.includes('signup.html') || text === 'Sign Up' || text === 'Sign Out';
		}) || null;
	}

	function updateNavbarAuth() {
		const authLink = findAuthNavLink();
		if (!authLink) return;

		const signedIn = isUserSignedIn();
		if (signedIn) {
			authLink.textContent = 'Sign Out';
			authLink.setAttribute('href', '#');
			authLink.style.cursor = 'pointer';
			authLink.removeEventListener('click', handleSignOut);
			authLink.addEventListener('click', handleSignOut);
		} else {
			authLink.textContent = 'Sign Up';
			authLink.setAttribute('href', 'signup.html');
			authLink.style.cursor = 'auto';
			authLink.removeEventListener('click', handleSignOut);
		}
	}

	function handleSignOut(event) {
		if (event) event.preventDefault();
		// Clear auth token only per spec
		try { localStorage.removeItem(AUTH_TOKEN_KEY); } catch (e) {}
		// reset in-memory progress state used by pages
		try { window.completedLetters = []; } catch (e) {}
		try { window.completedWords = []; } catch (e) {}
		updateNavbarAuth();
		// Reload to ensure UI resets immediately and pages reinitialize
		location.reload();
	}

	window.addEventListener('storage', function(event) {
		if (event.key === AUTH_TOKEN_KEY || event.key === USER_EMAIL_KEY) {
			updateNavbarAuth();
		}
	});

	window.addEventListener('focus', updateNavbarAuth);

	function init() {
		updateNavbarAuth();
	}

	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', init);
	} else {
		init();
	}

	window.updateNavbarAuth = updateNavbarAuth;
	window.isUserSignedIn = isUserSignedIn;
	window.handleSignOut = handleSignOut;
})();
