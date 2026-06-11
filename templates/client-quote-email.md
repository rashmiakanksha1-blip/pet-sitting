# Client quote — PDF + email

Use after `/check-booking` confirms dates are free and you want to send a quote.
**You send the email** with the PDF attached.

---

## Step 1 — Agent generates the PDF

Use **/send-quote** in chat — the agent runs everything and gives you the PDF path. You never run commands.

---

## Step 2 — Email to send (attach the PDF)

**Subject:** `Your pet sitting quote — [Client name]`

**Body:**

```
Hi [Client name],

Thank you for your enquiry about care for [pet name].

Good news — I'm available for those dates. Please find your quote attached as a PDF.

Pet: [cat/dog] · [pet name]
Dates: [start] – [end]
Service: [overnight stay / daily visit]
Total: £[total]

Please reply to confirm if you'd like to go ahead, and I'll reserve those dates for you.

Best,
Pet Sitters Club
petsittersclublondon@gmail.com
```

**Attach:** the PDF from `pet-sitting/receipts/output/`

---

## Rates used (GBP)

| Period | Visit | Overnight |
|--------|-------|-----------|
| Off-peak (Mon–Fri, not bank holidays) | £13 | £25 |
| Peak (Sat–Sun) | £14 | £27 |
| Super peak (bank holidays, 24 Dec–1 Jan) | £16 | £30 |

Extra pets: +£5 per visit day / +£8 per overnight night.
