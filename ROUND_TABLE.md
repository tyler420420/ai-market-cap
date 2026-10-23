# Daily Round Table — standing protocol

**Goal: the most $5/month subscribers possible.**

The chain we are optimizing, in order:

    followers -> views -> users (free signups) -> subscribers -> $5 MRR

Every meeting starts with `measure_funnel.py`, which reports all five links with
deltas since the last run. Everything else in the meeting is downstream of that
table.

---

## The rules

**1. One constraint. Not ten.**
A funnel is a chain, not a bucket list. Everything upstream of the weakest link
is worth nothing until that link moves. Every meeting identifies THE single
constraint and attacks only that. Ten parallel tasks means none of them finish.

**2. Check yesterday's commitment FIRST, before any new work.**
A meeting that only adds tasks and never closes them is a broadcast. The first
item is: did last meeting's deliverable actually land, and can we measure that
it did? Unmet commitments get escalated, not quietly replaced.

**3. UNKNOWN is never reported as 0.**
Zero means "measured, and nobody did it." UNKNOWN means "we cannot see." These
are different facts. A blind metric that gets reported as zero is how a business
believes it has no customers when it actually has customers it cannot count.

**4. Measure the artifact, not the intent.**
The deployed site, the live API, the real Stripe number. Never a source-level
check standing in for a customer-visible result. Three defects shipped as "done"
because the source was correct while the artifact was stale.

**5. Safety outranks growth, permanently.**
Never trade a safety property for a metric. Never put a placeholder in a
compliance field. Never email the 4,272 purchased lead addresses. Never wire
credentials into an unattended job. If growth requires breaking one of these,
growth loses.

**6. No invented numbers.**
Every figure traces to scanner output, /wins, Stripe live, or a cited filing.
Assumptions are labelled as assumptions. A metric nobody can source does not go
in the table — it goes in a "we cannot measure this" line.

**7. Short reports.**
One line per lane. One constraint. One owner. One deliverable. Then the marker.
Nobody transcribes a whole transcript.

---

## The funnel as measured on 2026-10-23 08:10 PT (baseline)

| link | value | note |
|---|---|---|
| followers | 114 | Bluesky, 6 days old, ~19/day average, decelerating to ~12/day. Flat. |
| views | 382 | **not a trustworthy number** — see "the counter counts our own tooling" below |
| users | **UNKNOWN** | blind spot: export is 403, no EMAIL_EXPORT_TOKEN on Railway |
| subscribers | 1 | one paying person; he holds 2 subscriptions on 1 email. Flat. |
| mrr | $10 | Flat. |

Two numbers in that table are worse than they look, and a meeting that trusts
them will chase the wrong thing.

**The views counter counts our own tooling.** Measured 2026-10-23: one browser-UA
GET of the homepage adds **7 hits** to the "human page views" number. 76 scripts
in this repo hit the live domain and 31 of them send a real Chrome User-Agent,
so our own audits are the largest single source of views. The +261 views on
2026-10-23 (121 -> 382) is mostly us. The honest read of that day is 22 unique
visitor buckets, and our own machine is one of them.

**The views counter also double-counts.** `all_time = baseline + since_boot`,
and `sync_visitor_baseline.py` writes the live `all_time` straight back into
the baseline without resetting `since_boot`, so every sync folds the live
counter into the floor a second time. The true all-time is lower than reported.

**Signups are captured and then destroyed.** `email_list.json` is gitignored
(PII rule), so it lives only on the container and dies with every Railway
deploy. The hourly `pull_email_list.py` has never succeeded because
`EMAIL_EXPORT_TOKEN` is not set on the service. The free-alert drip is wired
and gated on that same token, so it has never sent anything. The pipeline from
"a human signs up" to "a reachable, emailable, convertible lead" is built and
switched off at exactly one variable.

### What this baseline already says

**The chain is severed at link 1 → link 2.** 114 followers and a views number
that is mostly our own tooling is not a funnel, it is a coincidence — and the
reason is structural: the Bluesky account posts zero links, by standing safety
policy. An audience with no doorway cannot become traffic. That is a policy
decision, not a bug, and it belongs to Tyler.

**Second: replies earn zero replies back.** CMO measured 73 consecutive posts
with 0 replies received. The account broadcasts and nobody talks back, so
nothing compounds.

**Third, and this is the constraint as of 2026-10-23: the middle of the funnel
is unmeasured.** Signups are captured into a gitignored file and destroyed on
every deploy. We cannot say whether it is 0 people or 900 people. That is the
highest-priority *unknown*, because growth work upstream of a blind middle is
guessing: "no traffic" and "traffic that does not convert" need opposite fixes
in opposite lanes, and the funnel table cannot tell them apart.

The unblock for the blind middle is small and mostly sits with Tyler: one
`EMAIL_EXPORT_TOKEN` value, already in `alert.env`, pasted into the Railway
service. That opens the export (403 → 200), lets the hourly pull write the
durable local list, and satisfies the one-click-unsubscribe gate that is
currently holding the drip closed. The part that is *not* Tyler's is making
the count survive a deploy, which is the current commitment (2026-10-23-b).

---

## Standing roles

| lane | session | owns |
|---|---|---|
| CTO | `mvs_41a119d03ae849d59a2cdecd57e77d10` | site, scanner, deploy, guards |
| CMO | `mvs_938621b5d04b4bbdb4f8ca92a762a5e5` | Bluesky audience |
| SEO | `mvs_6a2f35fa54184d95822ea27062c969d3` | articles, indexing, organic |
| EMO | `mvs_acae3ae4047947888800c911d0705280` | email, opt-out, compliance |

Never cross-edit another lane's files. Cross-lane work goes through the CEO.

---

## Probes the round table must never skip

- `git rev-list --left-right --count origin/master...master` must read `0  0`.
  A commit that is not pushed is not shipped. This has been caught by hand
  three times in one night.
- Send a lane a question and read the REPLY. Never judge liveness from a status
  string — those record the last completed turn's error, not current capability.
- Send a real browser User-Agent when probing live HTTP. Cloudflare returns 1010
  to the default urllib agent and it reads exactly like a dead site.