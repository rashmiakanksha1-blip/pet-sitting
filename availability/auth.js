const AUTH_PIN_KEY = 'paws-stay-admin-pin';
const AUTH_SESSION_KEY = 'paws-stay-admin-session';

function isAuthenticated() {
  return sessionStorage.getItem(AUTH_SESSION_KEY) === 'true';
}

function getStoredPin() {
  return localStorage.getItem(AUTH_PIN_KEY);
}

function setPin(pin) {
  localStorage.setItem(AUTH_PIN_KEY, pin);
}

function login(pin) {
  const stored = getStoredPin();
  if (!stored) {
    if (!pin || pin.length < 4) {
      return { ok: false, msg: 'Choose a PIN with at least 4 characters.' };
    }
    setPin(pin);
    sessionStorage.setItem(AUTH_SESSION_KEY, 'true');
    return { ok: true, setup: true };
  }
  if (pin === stored) {
    sessionStorage.setItem(AUTH_SESSION_KEY, 'true');
    return { ok: true };
  }
  return { ok: false, msg: 'Incorrect PIN.' };
}

function logout() {
  sessionStorage.removeItem(AUTH_SESSION_KEY);
  location.href = 'index.html';
}

function requireAuth() {
  if (!isAuthenticated()) {
    const page = location.pathname.split('/').pop() || 'bookings.html';
    const qs = location.search ? location.search.slice(1) : '';
    const ret = qs ? `${page}?${qs}` : page;
    location.replace(`login.html?return=${encodeURIComponent(ret)}`);
  }
}
