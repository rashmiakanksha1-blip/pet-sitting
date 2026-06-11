const RATES = {
  'off-peak': { visit: 13, overnight: 25, label: 'Off-peak' },
  peak:       { visit: 14, overnight: 27, label: 'Peak' },
  'super-peak': { visit: 16, overnight: 30, label: 'Super peak' },
};

const EXTRA_PET = { visit: 5, overnight: 8 };

const STORAGE_KEYS = {
  availability: 'paws-stay-availability',
  bookings: 'paws-stay-bookings',
  pricing: 'paws-stay-pricing-overrides',
  receipts: 'paws-stay-receipts',
  inquiriesDismissed: 'paws-stay-inquiries-dismissed',
  inquiriesQuoted: 'paws-stay-inquiries-quoted',
};

const INQUIRIES_URL = 'data/inquiries.json';
const STORE_URL = 'data/store.json';

let storeEnquiries = [];

// Agent workflow — owner only says YES/NO at steps 3 and 6
const WORKFLOW_STATUS = {
  NEW: 'new',
  AWAITING_OWNER_DATES: 'awaiting_owner_dates',
  QUOTE_SENT: 'quote_sent',
  CLIENT_ACCEPTED: 'client_accepted',
  AWAITING_OWNER_CONFIRM: 'awaiting_owner_confirm',
  CONFIRMED: 'confirmed',
  DECLINED: 'declined',
  FEEDBACK_SENT: 'feedback_sent',
};

const BOOKING_STATUS = {
  QUOTED: 'quoted',
  CONFIRMED: 'confirmed',
};

const BOOKING_STATUS_LABELS = {
  quoted: 'Quote sent',
  confirmed: 'Confirmed',
};

const DEFAULT_BOOKINGS = [
  {
    id: 'ines-zelda-jun2026',
    clientName: 'Ines',
    petType: 'Dog',
    petName: 'Zelda',
    startDate: '2026-06-14',
    endDate: '2026-06-24',
    serviceType: 'overnight',
    extraPets: 0,
    notes: 'Overnight pet sitting',
    paymentStatus: 'pending',
    status: 'confirmed',
  },
];

function normalizeBooking(booking) {
  if (!booking.status) {
    booking.status = BOOKING_STATUS.CONFIRMED;
  }
  return booking;
}

function isConfirmedBooking(booking) {
  return booking?.status === BOOKING_STATUS.CONFIRMED;
}

function getConfirmedBookings() {
  return ensureBookings().filter(isConfirmedBooking);
}

function confirmBooking(bookingId) {
  const bookings = ensureBookings();
  const booking = bookings.find(b => b.id === bookingId);
  if (!booking) return null;
  booking.status = BOOKING_STATUS.CONFIRMED;
  saveBookings(bookings);
  syncAvailabilityFromBookings();
  persistOwnerStore();
  return booking;
}

function parseDateKey(key) {
  const [y, m, d] = key.split('-').map(Number);
  return new Date(y, m - 1, d);
}

function dateKeyFromDate(date) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
}

function getMondayWeekStartPad(date) {
  return (date.getDay() + 6) % 7;
}

const UK_BANK_HOLIDAYS = {
  2026: ['01-01', '04-03', '04-06', '05-04', '05-25', '08-31', '12-25', '12-26'],
};

function getUKBankHolidayKeys(year) {
  return (UK_BANK_HOLIDAYS[year] || []).map(md => `${year}-${md}`);
}

function isChristmasEveThroughNewYear(date) {
  const m = date.getMonth();
  const d = date.getDate();
  if (m === 11 && d >= 24) return true;
  if (m === 0 && d === 1) return true;
  return false;
}

function isSuperPeak(date) {
  const key = dateKeyFromDate(date);
  if (isChristmasEveThroughNewYear(date)) return true;
  return getUKBankHolidayKeys(date.getFullYear()).includes(key);
}

function isPeak(date) {
  if (isSuperPeak(date)) return false;
  const day = date.getDay();
  return day === 0 || day === 6;
}

function getTier(date) {
  if (isSuperPeak(date)) return 'super-peak';
  if (isPeak(date)) return 'peak';
  return 'off-peak';
}

function loadBookings() {
  try {
    const saved = localStorage.getItem(STORAGE_KEYS.bookings);
    if (saved) return JSON.parse(saved);
  } catch { /* empty */ }
  return null;
}

function saveBookings(bookings) {
  localStorage.setItem(STORAGE_KEYS.bookings, JSON.stringify(bookings));
}

function ensureBookings() {
  let bookings = loadBookings();
  if (!bookings || !bookings.length) {
    bookings = DEFAULT_BOOKINGS.map(b => ({ ...b }));
    if (bookings.length) saveBookings(bookings);
    return bookings;
  }
  return bookings.map(b => normalizeBooking({ ...b }));
}

function loadAvailability() {
  try {
    const saved = localStorage.getItem(STORAGE_KEYS.availability);
    return saved ? JSON.parse(saved) : {};
  } catch {
    return {};
  }
}

function saveAvailability(data) {
  localStorage.setItem(STORAGE_KEYS.availability, JSON.stringify(data));
}

function syncAvailabilityFromBookings() {
  const bookings = getConfirmedBookings();
  const availability = loadAvailability();

  Object.keys(availability).forEach(key => {
    if (availability[key] === 'booked') delete availability[key];
  });

  bookings.forEach(booking => {
    const start = parseDateKey(booking.startDate);
    const end = parseDateKey(booking.endDate);
    for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
      availability[dateKeyFromDate(d)] = 'booked';
    }
  });

  saveAvailability(availability);
  return availability;
}

function getBookingForDate(dateKey, options = {}) {
  const { confirmedOnly = false } = options;
  const bookings = ensureBookings();
  const d = parseDateKey(dateKey);
  const found = bookings.find(b => {
    const start = parseDateKey(b.startDate);
    const end = parseDateKey(b.endDate);
    return d >= start && d <= end;
  }) || null;
  if (!found) return null;
  if (confirmedOnly && !isConfirmedBooking(found)) return null;
  return found;
}

function eachDateInRange(startKey, endKey, fn) {
  const start = parseDateKey(startKey);
  const end = parseDateKey(endKey);
  for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
    fn(new Date(d), dateKeyFromDate(d));
  }
}

function countNights(startKey, endKey) {
  let count = 0;
  eachDateInRange(startKey, endKey, () => { count += 1; });
  return count;
}

function buildLineItems(booking) {
  const items = [];
  const extra = booking.extraPets || 0;
  const service = booking.serviceType || 'overnight';

  eachDateInRange(booking.startDate, booking.endDate, (date, key) => {
    const tier = getTier(date);
    const rate = RATES[tier][service];
    const extraCharge = extra * EXTRA_PET[service];
    items.push({
      date: key,
      dateLabel: date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' }),
      tier,
      tierLabel: RATES[tier].label,
      service,
      serviceLabel: service === 'overnight' ? 'Overnight stay' : 'Visit',
      rate,
      extraPets: extra,
      extraCharge,
      subtotal: rate + extraCharge,
    });
  });

  return items;
}

function calcBookingTotal(booking) {
  return buildLineItems(booking).reduce((sum, item) => sum + item.subtotal, 0);
}

function formatMoney(n) {
  return Number.isInteger(n) ? `£${n}` : `£${n.toFixed(2)}`;
}

function formatDateRange(startKey, endKey) {
  const opts = { month: 'short', day: 'numeric', year: 'numeric' };
  const s = parseDateKey(startKey).toLocaleDateString('en-US', opts);
  const e = parseDateKey(endKey).toLocaleDateString('en-US', opts);
  return `${s} – ${e}`;
}

function getPricingOverrides(bookingId) {
  try {
    const all = JSON.parse(localStorage.getItem(STORAGE_KEYS.pricing) || '{}');
    return all[bookingId] || {};
  } catch {
    return {};
  }
}

function buildLineItemsWithOverrides(booking) {
  const overrides = getPricingOverrides(booking.id);
  return buildLineItems(booking).map(item => {
    const ov = overrides[item.date];
    const subtotal = ov !== undefined && ov !== '' ? parseFloat(ov) : item.subtotal;
    return { ...item, subtotal };
  });
}

function calcBookingTotalWithOverrides(booking) {
  return buildLineItemsWithOverrides(booking).reduce((sum, item) => sum + item.subtotal, 0);
}

function loadReceipts() {
  try {
    const saved = localStorage.getItem(STORAGE_KEYS.receipts);
    return saved ? JSON.parse(saved) : [];
  } catch {
    return [];
  }
}

function saveReceipts(receipts) {
  localStorage.setItem(STORAGE_KEYS.receipts, JSON.stringify(receipts));
}

function getReceiptById(id) {
  return loadReceipts().find(r => r.id === id) || null;
}

function getReceiptForBooking(bookingId) {
  return loadReceipts().find(r => r.bookingId === bookingId) || null;
}

function nextReceiptNumber() {
  const receipts = loadReceipts();
  return `PS-${String(receipts.length + 1).padStart(4, '0')}`;
}

function createReceiptFromBooking(bookingId, replaceExisting) {
  const booking = ensureBookings().find(b => b.id === bookingId);
  if (!booking) return null;

  const receipts = loadReceipts();
  const existing = receipts.find(r => r.bookingId === bookingId);
  if (existing && !replaceExisting) return existing;

  const lineItems = buildLineItemsWithOverrides(booking);
  const receipt = {
    id: existing?.id || `receipt-${bookingId}`,
    bookingId,
    receiptNumber: existing?.receiptNumber || nextReceiptNumber(),
    createdAt: existing?.createdAt || new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    issuedDate: new Date().toISOString().split('T')[0],
    clientName: booking.clientName,
    petType: booking.petType,
    petName: booking.petName,
    startDate: booking.startDate,
    endDate: booking.endDate,
    serviceType: booking.serviceType,
    paymentStatus: booking.paymentStatus || 'pending',
    lineItems: lineItems.map(item => ({
      date: item.date,
      dateLabel: item.dateLabel,
      description: `${item.serviceLabel} — ${item.tierLabel} rate`,
      amount: item.subtotal,
    })),
    total: lineItems.reduce((sum, item) => sum + item.subtotal, 0),
  };

  if (existing) {
    const idx = receipts.indexOf(existing);
    receipts[idx] = receipt;
  } else {
    receipts.push(receipt);
  }
  saveReceipts(receipts);
  return receipt;
}

function getDismissedInquiryIds() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEYS.inquiriesDismissed) || '[]');
  } catch {
    return [];
  }
}

function dismissInquiryLocally(inquiryId) {
  const ids = getDismissedInquiryIds();
  if (!ids.includes(inquiryId)) {
    ids.push(inquiryId);
    localStorage.setItem(STORAGE_KEYS.inquiriesDismissed, JSON.stringify(ids));
  }
}

function getQuotedInquiryIds() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEYS.inquiriesQuoted) || '[]');
  } catch {
    return [];
  }
}

function markInquiryQuotedLocally(inquiryId) {
  const ids = getQuotedInquiryIds();
  if (!ids.includes(inquiryId)) {
    ids.push(inquiryId);
    localStorage.setItem(STORAGE_KEYS.inquiriesQuoted, JSON.stringify(ids));
  }
}

async function loadInquiriesFromFile() {
  try {
    const res = await fetch(`${INQUIRIES_URL}?t=${Date.now()}`);
    if (!res.ok) return [];
    const data = await res.json();
    const dismissed = getDismissedInquiryIds();
    const quotedLocal = getQuotedInquiryIds();
    return (data.inquiries || [])
      .filter(i => i.status !== 'dismissed' && !dismissed.includes(i.id))
      .map(i => ({
        ...i,
        status: quotedLocal.includes(i.id) || i.status === 'quoted' ? 'quoted' : i.status,
      }));
  } catch {
    return [];
  }
}

function countNewInquiries(inquiries) {
  return inquiries.filter(i => i.status === 'new').length;
}

function buildPricingUrlFromInquiry(inquiry) {
  const params = new URLSearchParams({ new: '1', inquiry: inquiry.id });
  if (inquiry.clientName) params.set('client', inquiry.clientName);
  if (inquiry.petName) params.set('pet', inquiry.petName);
  if (inquiry.petType) params.set('petType', inquiry.petType);
  if (inquiry.startDate) params.set('start', inquiry.startDate);
  if (inquiry.endDate) params.set('end', inquiry.endDate);
  if (inquiry.serviceType) params.set('service', inquiry.serviceType);
  if (inquiry.extraPets) params.set('extraPets', String(inquiry.extraPets));
  return `pricing.html?${params.toString()}`;
}

function getBookingEmail() {
  return (typeof SITE_CONFIG !== 'undefined' && SITE_CONFIG.bookingEmail) || 'hello@example.com';
}

function buildBookingMailtoUrl(selectedDates) {
  const email = getBookingEmail();
  const subject = SITE_CONFIG?.bookingInquirySubject
    || `Pet sitting inquiry — ${SITE_CONFIG?.businessName || 'booking'}`;
  const dateLine = selectedDates?.length
    ? `Dates I'm interested in: ${selectedDates.join(', ')}\n`
    : `Dates I'm interested in: \n`;
  const body = [
    `Hi,`,
    ``,
    `I'd like to enquire about pet sitting.`,
    ``,
    dateLine,
    `Pet name: `,
    `Pet type (dog / cat): `,
    `Breed / size (cats: all sizes · dogs: small breeds e.g. pug, terrier): `,
    `Service needed (visit / overnight): `,
    `Number of pets: `,
    `Anything else we should know: `,
    ``,
    `Thank you!`,
  ].join('\n');
  return `mailto:${encodeURIComponent(email)}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
}

const RECEIPT_EMAIL_TEMPLATES = {
  quote: {
    label: 'Price quote',
    subject: receipt => `Your pet sitting quote — ${receipt.clientName}`,
    build: (receipt) => {
      const lines = receipt.lineItems.map(l => `  ${l.dateLabel}: ${l.description} — ${formatMoney(l.amount)}`).join('\n');
      return [
        `Hi ${receipt.clientName},`,
        ``,
        `Thank you for your enquiry about care for ${receipt.petName}. Here is your quote:`,
        ``,
        `Pet: ${receipt.petType} · ${receipt.petName}`,
        `Dates: ${formatDateRange(receipt.startDate, receipt.endDate)}`,
        ``,
        lines,
        ``,
        `Total: ${formatMoney(receipt.total)}`,
        ``,
        `Please reply to confirm if you'd like to go ahead, and I'll reserve those dates for you.`,
        ``,
        `Best,`,
        `${SITE_CONFIG?.businessName || 'Paws & Stay'}`,
      ].join('\n');
    },
  },
  confirmed: {
    label: 'Booking confirmed',
    subject: receipt => `Booking confirmed — ${receipt.petName}`,
    build: (receipt) => [
      `Hi ${receipt.clientName},`,
      ``,
      `Lovely — your booking is confirmed!`,
      ``,
      `Pet: ${receipt.petType} · ${receipt.petName}`,
      `Dates: ${formatDateRange(receipt.startDate, receipt.endDate)}`,
      `Total: ${formatMoney(receipt.total)}`,
      ``,
      `I've marked these dates on my calendar. I'll be in touch closer to the start date with any final details.`,
      ``,
      `Best,`,
      `${SITE_CONFIG?.businessName || 'Paws & Stay'}`,
    ].join('\n'),
  },
  reminder: {
    label: 'Payment reminder',
    subject: receipt => `Payment reminder — receipt ${receipt.receiptNumber}`,
    build: (receipt) => [
      `Hi ${receipt.clientName},`,
      ``,
      `A friendly reminder about your pet sitting booking (${formatDateRange(receipt.startDate, receipt.endDate)}).`,
      ``,
      `Amount due: ${formatMoney(receipt.total)}`,
      `Receipt: ${receipt.receiptNumber}`,
      ``,
      `Please let me know if you have any questions.`,
      ``,
      `Best,`,
      `${SITE_CONFIG?.businessName || 'Paws & Stay'}`,
    ].join('\n'),
  },
};

function buildFeedbackEmail(booking) {
  const name = SITE_CONFIG?.businessName || 'Paws & Stay';
  return {
    subject: `How was your pet sitting with ${name}?`,
    body: [
      `Hi ${booking.clientName},`,
      ``,
      `I hope ${booking.petName} is settled back in after your trip.`,
      ``,
      `I'd really appreciate a few words about your experience — it helps me improve and lets other pet parents know what to expect.`,
      ``,
      `If you have a moment, please reply with:`,
      `  • How did ${booking.petName} seem during the stay?`,
      `  • Was communication clear and timely?`,
      `  • Would you book again?`,
      ``,
      `Thank you again for trusting me with ${booking.petName}.`,
      ``,
      `Warmly,`,
      name,
    ].join('\n'),
  };
}

function buildOwnerNotification(type, enquiry) {
  const dates = enquiry.startDate
    ? formatDateRange(enquiry.startDate, enquiry.endDate || enquiry.startDate)
    : 'dates TBC';
  if (type === 'new_enquiry') {
    return {
      subject: `Pet sitting enquiry — ${enquiry.clientName || 'new client'}`,
      body: [
        `New enquiry received.`,
        ``,
        `Client: ${enquiry.clientName || enquiry.fromName}`,
        `Pet: ${enquiry.petType || '—'} · ${enquiry.petName || 'TBC'}`,
        `Dates: ${dates}`,
        ``,
        `Check your calendar, then reply:`,
        `  YES — send them a price quote`,
        `  NO — decline this enquiry`,
      ].join('\n'),
    };
  }
  if (type === 'client_accepted') {
    return {
      subject: `Client accepted quote — ${enquiry.clientName}`,
      body: [
        `${enquiry.clientName} accepted the quote for ${enquiry.petName}.`,
        `Dates: ${dates}`,
        `Total: ${enquiry.quoteTotal ? formatMoney(enquiry.quoteTotal) : 'see quote'}`,
        ``,
        `Reply YES to confirm the booking (updates your calendar and the public availability page).`,
        `Reply NO to go back to the client.`,
      ].join('\n'),
    };
  }
  return { subject: 'Pet sitting update', body: '' };
}

function applyStoreData(store) {
  if (!store || typeof store !== 'object') return;
  if (Array.isArray(store.enquiries)) storeEnquiries = store.enquiries;
  if (Array.isArray(store.bookings)) {
    saveBookings(store.bookings.map(b => normalizeBooking({ ...b })));
  }
  if (store.availability && typeof store.availability === 'object') {
    saveAvailability(store.availability);
  }
}

function buildStoreSnapshot() {
  return {
    version: 1,
    enquiries: storeEnquiries,
    bookings: ensureBookings(),
    availability: loadAvailability(),
  };
}

function getLiveStoreUrl() {
  const cfg = typeof SITE_CONFIG !== 'undefined' ? SITE_CONFIG : {};
  const url = cfg.liveStoreUrl || '';
  // When served from a host other than Netlify (e.g. GitHub Pages mirror),
  // a relative function path won't exist — use the absolute Netlify function.
  const isRelative = url.startsWith('/');
  const onNetlify = typeof location !== 'undefined' && /netlify\.app$/.test(location.hostname);
  if (isRelative && !onNetlify && cfg.liveStoreUrlAbsolute) {
    return cfg.liveStoreUrlAbsolute;
  }
  return url;
}

function getStoreWriteKey() {
  return (typeof SITE_CONFIG !== 'undefined' && SITE_CONFIG.storeWriteKey) || '';
}

function storeHasCalendarData(store) {
  if (!store || typeof store !== 'object') return false;
  if (Array.isArray(store.bookings) && store.bookings.length) return true;
  return Object.keys(store.availability || {}).length > 0;
}

function showSyncStatus(message) {
  const el = document.getElementById('syncStatus');
  if (!el) return;
  el.textContent = message;
  if (message) {
    window.clearTimeout(showSyncStatus._timer);
    showSyncStatus._timer = window.setTimeout(() => {
      el.textContent = '';
    }, 2500);
  }
}

async function fetchLiveStore() {
  const liveUrl = getLiveStoreUrl();
  if (!liveUrl) return null;
  try {
    const res = await fetch(`${liveUrl}?t=${Date.now()}`);
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

async function pushStoreToCloud() {
  const liveUrl = getLiveStoreUrl();
  if (!liveUrl) return false;
  const pin = typeof getStoredPin === 'function' ? getStoredPin() : '';
  const writeKey = getStoreWriteKey();
  try {
    const res = await fetch(liveUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pin, writeKey, store: buildStoreSnapshot() }),
    });
    return res.ok;
  } catch {
    return false;
  }
}

async function persistOwnerStore() {
  if (typeof isAuthenticated !== 'function' || !isAuthenticated()) return false;
  if (!getLiveStoreUrl()) return false;
  showSyncStatus('Saving…');
  const ok = await pushStoreToCloud();
  showSyncStatus(ok ? 'Saved' : 'Could not save — check connection');
  return ok;
}

async function hydrateFromStore() {
  const liveStore = await fetchLiveStore();
  if (storeHasCalendarData(liveStore)) {
    applyStoreData(liveStore);
    return true;
  }

  try {
    const res = await fetch(`${STORE_URL}?t=${Date.now()}`);
    if (!res.ok) return false;
    applyStoreData(await res.json());
    if (typeof isAuthenticated === 'function' && isAuthenticated()) {
      await pushStoreToCloud();
    }
    return true;
  } catch {
    return false;
  }
}

function buildReceiptMailtoUrl(receipt, templateKey) {
  const tpl = RECEIPT_EMAIL_TEMPLATES[templateKey] || RECEIPT_EMAIL_TEMPLATES.quote;
  const subject = tpl.subject(receipt);
  const body = tpl.build(receipt);
  return `mailto:?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
}

function updateReceiptPayment(receiptId, status) {
  const receipts = loadReceipts();
  const receipt = receipts.find(r => r.id === receiptId);
  if (!receipt) return;

  receipt.paymentStatus = status;
  receipt.updatedAt = new Date().toISOString();
  saveReceipts(receipts);

  const bookings = ensureBookings();
  const booking = bookings.find(b => b.id === receipt.bookingId);
  if (booking) {
    booking.paymentStatus = status;
    saveBookings(bookings);
  }
}
