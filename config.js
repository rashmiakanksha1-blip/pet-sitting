// ← Edit these to customise your site
const SITE_CONFIG = {
  siteVersion: '10 Jun 2026 (ai)',
  businessName: 'Pet Sitters Club',
  bookingInquirySubject: 'Pet sitting inquiry - Pet Sitters Club',
  tagline: 'Sit, stay. We\'ll take it from here',
  petsInfo: {
    cats: 'All sizes welcome',
    dogs: 'Small breeds · pug-sized & similar',
  },

  // ONE link for word-of-mouth — share this everywhere; it never changes.
  // After you host on Netlify, paste your real URL here (see netlify.toml).
  // Netlify deploys are blocked until credits are restored — mirror is current.
  publicBookingUrl: 'https://rashmiakanksha1-blip.github.io/pet-sitting/',

  contactEmail: 'petsittersclublondon@gmail.com',
  bookingEmail: 'petsittersclublondon@gmail.com',
  // Email fallback for agent notifications (Telegram preferred — see scripts/.env)
  ownerNotifyEmail: 'petsittersclublondon@gmail.com',

  // Show the £ rates table to clients on the public calendar
  showRatesToPublic: true,

  // Live calendar — owner updates on the site sync here automatically (no Netlify dashboard).
  liveStoreUrl: '/.netlify/functions/store',
  // Used when the site is served off-Netlify (e.g. the GitHub Pages mirror) so the
  // calendar still reads/writes the same live data via the Netlify function (CORS-enabled).
  liveStoreUrlAbsolute: 'https://petsittersclublondon.netlify.app/.netlify/functions/store',
  storeWriteKey: 'psc-live-sync-7k9m2xq',

  // Names shown in browser tab
  customerPageTitle: 'Check availability',
  ownerPageTitle: 'Owner login',
};
