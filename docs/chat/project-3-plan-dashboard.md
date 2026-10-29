# Thread: Plan the webhook dashboard

Claude Code project on claude.ai · "Benji exercise" · sub-thread

## 🧑 User

in another thread we gonna summarize what we need for the dashboard, also you can check the api plan we have written for api references

## 🤖 Claude

I’ll read the API plan and your handover, then summarize the dashboard’s screens, data flow and live updates for you to challenge.

I read the API plan on PR #3 (`docs/API_PLAN.md`, and `docs/PLAN.md:145` for the dashboard section) plus what’s already scaffolded: the shell, `apiFetch`/`ApiError`, the Vue Query plugin and the `@repo/ui` primitives.

**What we’re building:** three surfaces on top of `app/api/` (typed fetch), `app/composables/` (query hooks, one key factory, SSE into the cache) and render-only components.

1. **Deliveries** (home): a live table with status, attempts `2/5`, a next-retry countdown, rows that expand into payload + attempt log, Replay on failed rows, and the status filter kept in the URL.
2. **Endpoints**: a list with an enable switch, plus a create dialog that shows the secret once.
3. **Fire event**: a sheet with type, a prefilled JSON payload and the idempotency key, ending in a “created, N deliveries” or “deduplicated” banner.

**Where I’d push back on the current plan:**
• _“Write every SSE message into the cache” breaks with filters._ A new delivery would have to be placed into every filtered list in the right position. I’d patch only rows already in the cache (with the version check) and invalidate the list when an unknown id shows up. It’s simpler and can’t be wrong.
• _The secret must never touch the query cache._ The create response stays in the dialog’s local state. The list gets refetched, never `setQueryData` from that response.
• _Idempotency key UX:_ a new key per intended action, regenerated when the type or payload changes, plus an explicit “Re-submit same key” button. Without that button a reviewer can’t see dedupe working.
• _Cut editing event types after creation._ PATCH supports it, but toggling is what’s asked. Delete and recreate covers it.
• _Sheet rather than a page for firing,_ because you watch the rows appear behind it. That’s the demo.
• _Sequencing:_ the dashboard waits on the generated `schema.d.ts`. I’d ask the API thread to run `gen:api` after step 4 rather than only at step 9.

Which of these do you disagree with? I’ll write the plan doc once we’ve settled them.

## 🧑 User

I'd like to clearly separate the "exercise testing aspect" of the dashboard from the "real dashboard" that could be a real dashboard for a customer -> I'd build the dashboard and on its side, in a full height card always visible on any page of the dashboard I'd put our testing widgets, fire an event with data type etc, or retry an event with the same idempotency key, etc

what I have in mind is a nice all in one page interface, simple

logo on top left, with a few menu on its right

on the same page small widgets cards, deliveries and subscriptions, with basic informations, each card can be opened in a dedicated page

## 🤖 Claude

I like the split, and it matches how the product really works. Benji fires events and customers only receive them, so firing and re-submitting with an idempotency key are things only we need. Keeping them in a side panel makes the “real” dashboard honest. Replay stays in the real dashboard, because a customer would want it. The mock receiver URLs move to the panel too, with copy buttons, so the create dialog stays a plain URL field.

Three pushbacks:
• **Always visible eats the width the deliveries page needs.** A table with expandable rows and an attempt log needs room. I’d make the panel open by default with a toggle in the header, and turn it into a sheet on narrow screens.
• **“Subscriptions” vs “Endpoints”.** In the API, `subscriptions` is the link table and the resource is an endpoint. If the UI says subscriptions, the card, the page and the API use different words for the same thing. I’d keep “Endpoints” everywhere, like Stripe does.
• **The overview cards need a clear job or they just repeat the pages.** I’d have the deliveries card show the latest 5 rows, updating live, and the endpoints card show the list with enabled switches, each card with “View all”. Status counts (“3 failed”) would need a small stats route from the API, because counting a limited list gives wrong numbers. Worth it, or skip?

Layout as I picture it: logo, then Overview · Deliveries · Endpoints, then the panel toggle and theme on the right. Overview is the two cards, and the panel holds Fire event, Re-submit and Mock receivers.

## 🧑 User

Always visible eats the width the deliveries page needs. A table with expandable rows and an attempt log needs room. I’d make the panel open by default with a toggle in the header, and turn it into a sheet on narrow screens. -> let's start with what I say and we can change later on

“Subscriptions” vs “Endpoints”. In the API, subscriptions is the link table and the resource is an endpoint. If the UI says subscriptions, the card, the page and the API use different words for the same thing. I’d keep “Endpoints” everywhere, like Stripe does. -> not sure here, an endpoint could be linked to multiple event type and we want to show that in a list no?

3 - worth it

## 🤖 Claude

Deal on the panel: always visible for now, and we revisit once we see it with real rows.

On naming: yes, we show the event types, and that’s exactly why I’d still call the row an endpoint. Each row is one URL with its event types as chips (`reward_transaction_created`, `campaign_updated`). A list with one row per subscription, meaning one per (URL, event type) pair, would repeat the same URL several times. Its enable switch and its secret also belong to the URL, not to the pair, so the thing you act on is the endpoint. That said, “Subscriptions” works as a customer-facing label if you see it as “where I receive my events”. What I want to avoid is mixing words: either the card, the page and the nav all say Subscriptions with endpoint rows inside, or they all say Endpoints. Which do you prefer?

For the counts, I’ve asked the API thread for a small stats route. Once you pick the name, I’ll write the plan doc.

## 🧑 User

ok if you say so we keep endpoints, but I thought we could enable/disable an endpoint specific type, like an endpoint could still get the webhook for "new points" but not anymore the webhook for "removed points"

## 🤖 Claude

You’re right, and that changes one thing I said: I proposed cutting the editing of event types, and your example is exactly why it belongs in. Stopping “removed points” while keeping “new points” is a real customer need.

The good news is that the API already does it, with no change needed. `PATCH /api/endpoints/{id}` with `event_types: [...]` adds or removes the link rows. So the model ends up in two levels:
• **The endpoint switch** pauses everything for that URL (the secret and the URL stay the same).
• **A switch per event type** on the endpoint’s page subscribes it to that type or unsubscribes it. Those per-type switches are the “subscriptions”, so the word still shows up where it fits.

One behaviour to know: unsubscribing a type only affects future events. Deliveries already queued for that type still go out. I think that’s correct, the same as Stripe.

I’ll keep “Endpoints” as the name, with the per-type switches on the endpoint page. I’m writing the plan doc now unless you want to change something.

## 🧑 User

well we can use subscriptions then? because we gonna need an "endpoints" list as well somewhere to create and edit them

## 🤖 Claude

I’d still say one list is enough, and here’s the test: what would a “Subscriptions” list show that the Endpoints list doesn’t? Each endpoint row already carries its event types as chips, a create button sits on top, and clicking a row opens the endpoint page where you edit its types and toggle it. Two pages showing the same rows means two places to keep in sync, and a reviewer will ask why.

There is one genuinely different view we could call Subscriptions: one row per **event type**, listing which endpoints receive it (“who gets `reward_transaction_created`?”). It answers a real question, but no requirement asks for it. I’d put it in the next steps, not the build.

So my proposal is one Endpoints page (list + create, with an endpoint page for editing), and the overview card links to it. Were you picturing the per-event-type view, or the same endpoint rows under a second name?

Meanwhile I’ve drafted the plan doc on that basis. I’ll open the PR once we settle this.

## 🧑 User

my point is that in my head an endpoint is simply a URL and a secret, when the user creates a new subscription he needs to pick an endpoint and an event type

when he does that I dont want him to write the URL again for an endpoint he has already created, therefore he will have a "picker" with a list of ENDPOINTS with their urls

## 🤖 Claude

Got it, that’s a clearer picture. The data model already matches it: an endpoint is a URL + secret, and a subscription is an (endpoint, event type) row. What differs is only where the user starts.

The flow you describe never makes anyone retype a URL in my version either. To subscribe an existing endpoint to a new type, you open the endpoint and switch the type on. Your version starts from the subscription instead: “New subscription”, pick an endpoint, pick a type. Both work. Here’s the trade-off:

• **Endpoint-first** (mine): one page, and the brief is phrased this way (“registers endpoints, each subscribed to 1+ event types”). An endpoint can never sit there receiving nothing, because creation requires at least one type.
• **Subscription-first** (yours): two pages, Endpoints (URL + secret, create, enable) and Subscriptions (pairs, with the picker). It reads more naturally once a customer has many types. It also allows an endpoint with zero subscriptions, which is fine but needs an empty state (“not subscribed to anything”).

Yours needs **no API change**. [Edit: one small API change. Today `event_types` must have at least 1 item on create and on PATCH, so an endpoint with no subscriptions is rejected. Allowing 0 is a one-line change in each place, plus a test.] The Subscriptions page is a client-side view over `GET /api/endpoints`, and “add” or “remove” is a `PATCH event_types` on the chosen endpoint. The cost is one extra page and the picker, maybe 30 to 45 minutes.

If you want it, I’ll go with yours. It’s a fair product call, and it gives the “Subscriptions” name a real home. Shall I update the plan?

(edited)

## 🧑 User

ok now I get your point, let's do what you want

(edited)

## 🤖 Claude

Endpoint-first it is, so the plan already matches. I stopped when you rejected my last step, which was adding the per-event-type Subscriptions view as a next step in the plan and pushing it.

The draft is on the branch as `docs/DASHBOARD_PLAN.md`, with no PR yet. Should I open the PR as it is, or do you want to read it first or change something?

## 🧑 User

open the PR

## 🤖 Claude

The PR is up: [#5 Add the dashboard build plan](https://github.com/polgiron/benji-exercise/pull/5). It’s docs only, so I didn’t run the typecheck, lint or tests, but Prettier passes on the file. [Edit: squash-merged into main at your request.]

(edited)

## 🧑 User

merge it

## 🤖 Claude

New
- Read the repo setup and the API plan
- Summarize the dashboard scope in chat, with points to challenge
- Settle layout, stats route and naming with polo
- Draft docs/DASHBOARD_PLAN.md
- Open the PR (#5) and merge it

I squash-merged #5, so `docs/DASHBOARD_PLAN.md` is now on main. One thing to know: it links to `docs/API_PLAN.md`, which only reaches main once the API PR #3 is merged. The plan’s build steps also start after that merge. [Edit: #3 is merged now, so the link works and the dashboard build can start from main.]

(edited)
