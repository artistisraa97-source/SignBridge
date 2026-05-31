// Shared API utility for authenticated requests
(function() {
	window.apiCall = async function(endpoint, method = 'GET', data = null) {
		// Use SB.authToken when available (read once per session)
		const token = (window.SB && window.SB.authToken) || localStorage.getItem('auth_token');
		if (window.SB && !window.SB.authToken && token) window.SB.authToken = token;
		const headers = {
			'Content-Type': 'application/json'
		};
		
		if (token) {
			headers['Authorization'] = `Bearer ${token}`;
		}

		const options = {
			method,
			headers
		};

		if (data && (method === 'POST' || method === 'PUT')) {
			options.body = JSON.stringify(data);
		}

		try {
			const response = await fetch(endpoint, options);
			const json = await response.json();
			
			if (response.status === 401) {
				// Token expired or invalid: clear auth token only
				try { localStorage.removeItem('auth_token'); } catch (e) {}
				if (window.updateNavbarAuth) window.updateNavbarAuth();
				throw new Error('Session expired. Please sign in again.');
			}
			
			return { status: response.status, data: json };
		} catch (error) {
			console.error('API call error:', error);
			throw error;
		}
	};

	// Single-page session manager to read auth once and fetch progress once per page session
	window.SB = window.SB || {
		authToken: null,
		_progressPromise: null,
		progress: null,
		init: async function() {
			if (this.authToken === null) {
				this.authToken = localStorage.getItem('auth_token') || null;
			}
			if (!this.authToken) return this;
			if (!this._progressPromise) {
				this._progressPromise = (async () => {
					try {
						const p = await window.getUserProgress();
						this.progress = p || null;
						return this.progress;
					} catch (e) {
						this.progress = null;
						return null;
					}
				})();
			}
			await this._progressPromise;
			return this;
		},
		clear: function() { this.authToken = null; this.progress = null; this._progressPromise = null; }
	};

	window.saveProgress = async function(progressData) {
		try {
			const result = await window.apiCall('/api/progress/update', 'POST', progressData);
			if (result.status === 200 && result.data.success) {
				return result.data.progress;
			}
		} catch (error) {
			console.error('Failed to save progress:', error);
		}
		return null;
	};

	window.completeWord = async function(word) {
		try {
			const result = await window.apiCall('/api/progress/word', 'POST', { word });
			if (result.status === 200 && result.data.success) {
				return result.data.progress;
			}
		} catch (error) {
			console.error('Failed to mark word complete:', error);
		}
		return null;
	};

	window.masterletter = async function(letter) {
		try {
			const result = await window.apiCall('/api/progress/letter', 'POST', { letter });
			if (result.status === 200 && result.data.success) {
				return result.data.progress;
			}
		} catch (error) {
			console.error('Failed to mark letter mastered:', error);
		}
		return null;
	};

	window.submitQuizScore = async function(score, total) {
		try {
			const result = await window.apiCall('/api/progress/quiz', 'POST', { score, total });
			if (result.status === 200 && result.data.success) {
				return result.data.progress;
			}
		} catch (error) {
			console.error('Failed to submit quiz score:', error);
		}
		return null;
	};

	window.getUserProgress = async function() {
		try {
			const result = await window.apiCall('/api/progress/me', 'GET');
			if (result.status === 200 && result.data.success) {
				return result.data.progress;
			}
		} catch (error) {
			console.error('Failed to fetch user progress:', error);
		}
		return null;
	};
})();
