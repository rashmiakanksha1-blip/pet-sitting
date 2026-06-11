// ← Edit these to customise your site
const SITE_CONFIG = {
  siteVersion: 'Version 2',
  designVersion: 2,
  businessName: 'Pet Sitters Club',
  bookButtonLabel: 'Book my slot',
  bookingInquirySubject: 'Pet sitting inquiry - Pet Sitters Club',
  tagline: 'Sit, stay. We\'ll take it from here',
  petsInfo: {
    cats: 'All sizes welcome',
    dogs: 'Small breeds · pug-sized & similar',
  },

  // Your own domain — no personal GitHub username in the link.
  // Run: bash scripts/setup-custom-domain.sh www.petsittersclub.co.uk
  customDomain: '',

  // ONE link for word-of-mouth — filled automatically when customDomain is set.
  publicBookingUrl: 'https://rashmiakanksha1-blip.github.io/pet-sitting/book/',

  contactEmail: 'petsittersclublondon@gmail.com',
  bookingEmail: 'petsittersclublondon@gmail.com',
  ownerNotifyEmail: 'petsittersclublondon@gmail.com',

  showRatesToPublic: true,

  liveStoreUrl: '/.netlify/functions/store',
  liveStoreUrlAbsolute: 'https://petsittersclublondon.netlify.app/.netlify/functions/store',
  storeWriteKey: 'psc-live-sync-7k9m2xq',

  customerPageTitle: 'Check availability',
  ownerPageTitle: 'Owner login',
};

(function applyCustomDomain() {
  if (!SITE_CONFIG.customDomain) return;
  const host = SITE_CONFIG.customDomain.replace(/^https?:\/\//, '').replace(/\/+$/, '');
  SITE_CONFIG.publicBookingUrl = `https://${host}/book/`;
  if (typeof location !== 'undefined' && /\.github\.io$/i.test(location.hostname)) {
    location.replace(SITE_CONFIG.publicBookingUrl + location.search + location.hash);
  }
})();
