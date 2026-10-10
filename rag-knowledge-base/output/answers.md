# RAG knowledge base - answers (real run)

Models: all-minilm:33m (embeddings), qwen2.5:1.5b-instruct (answers), both local via Ollama. Top-k = 4.

**Score (rule-based, no LLM judge):** 5/5 answerable questions answered with the expected document cited; 2/2 unanswerable questions correctly abstained. Latency per question (embed + generate, as measured by Ollama): median 8.79s, max 17.7s.

## T1. How many unused Meridian PTO days can be carried into the next calendar year?

**ANSWER** (PASS; expected ANSWER) - 2.08s

> Up to 5 unused PTO days may be carried over into the next calendar year. [meridian-pto-policy#carryover]

Top-k retrieved: meridian-pto-policy#carryover (0.647), meridian-pto-policy#unused-pto-payout (0.449), meridian-pto-policy#accrual (0.443), meridian-hr-faq#payroll-schedule (0.412)

## T2. What does error code E12 mean on the Cascade POS terminal?

**ANSWER** (PASS; expected ANSWER) - 4.37s

> Error E12 indicates the terminal has lost sync with the manager portal and transactions will queue locally until connectivity is restored. [cascade-pos-manual#support-contact]

Top-k retrieved: cascade-pos-manual#error-codes (0.791), cascade-pos-manual#support-contact (0.521), cascade-pos-manual#setup (0.47), cascade-pos-manual#hardware-maintenance (0.438)

## T3. What encryption does CloudVault use to protect backed-up files?

**ANSWER** (PASS; expected ANSWER) - 17.7s

> CloudVault uses AES-256 encryption client-side before uploading data. [solstice-backup-manual#encryption]

Top-k retrieved: solstice-backup-manual#encryption (0.801), solstice-backup-manual#overview (0.657), solstice-backup-manual#supported-platforms (0.58), solstice-backup-manual#restore-procedure (0.556)

## T4. Under Meridian's current remote work policy, does the company provide a home office equipment stipend, and if so how much?

**ANSWER** (PASS; expected ANSWER) - 7.71s

> Yes, Meridian provides a one-time home office stipend of $500 for approved remote employees, covering desk, chair, or monitor purchases. Receipts must be submitted within 60 days of approval. [meridian-remote-work-v2#equipment]

Top-k retrieved: meridian-remote-work-v2#equipment (0.872), meridian-remote-work-v1#equipment (0.817), meridian-hr-faq#remote-work-faq (0.782), meridian-remote-work-v2#home-office-stipend (0.711)

## T5. Under Cascade's current returns policy, what is the standard return window, and is there an exception for electronics?

**ANSWER** (PASS; expected ANSWER) - 15.58s

> The standard return window is 45 days, and electronics must be returned within 14 days. [cascade-returns-policy-v2#return-window] [cascade-returns-policy-v2#exceptions]

Top-k retrieved: cascade-returns-policy-v2#return-window (0.559), cascade-returns-policy-v1#return-window (0.53), cascade-support-faq#warranty (0.509), cascade-returns-policy-v2#exceptions (0.433)

## T6. Does Solstice Systems offer a mobile app version of SecureLink for iOS or Android?

**ABSTAIN** (PASS; expected ABSTAIN) - 8.79s

> Not in the documents.

Top-k retrieved: solstice-vpn-manual#overview (0.632), solstice-vpn-manual#installation (0.624), solstice-faq#general (0.599), solstice-faq#technical-support (0.499)

## T7. What is Meridian Health Partners' policy on paid jury duty leave?

**ABSTAIN** (PASS; expected ABSTAIN) - 11.1s

> Not in the documents.

Top-k retrieved: meridian-hr-faq#parental-leave (0.611), meridian-hr-faq#payroll-schedule (0.575), meridian-remote-work-v2#purpose (0.574), meridian-remote-work-v1#purpose (0.561)

