# Client cancellation email

Use with **/cancel-booking** — give dates only; the agent finds affected clients.

---

**Subject:** `Booking cancelled — [pet name]`

**Body:**

```
Hi [Client name],

I'm sorry to let you know that your pet sitting booking for [pet name] ([start] – [end]) has been cancelled.

[Optional reason]

Those dates are now released on my calendar. If you'd like to rebook for different dates, just reply and I'll check availability.

Sorry for any inconvenience.

Best,
Pet Sitters Club
petsittersclublondon@gmail.com
```

---

## What the agent does

1. You send **dates only** (single day or range)
2. Agent finds **all confirmed bookings** that overlap those dates (can be multiple clients)
3. Agent writes a **cancellation email per client**
4. Agent cancels bookings, frees dates, publishes live

**Example input:**
```
Dates: 3 Jul 2026 to 10 Jul 2026
Reason: schedule conflict
```
