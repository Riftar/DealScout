# DealScout

DealScout finds the listings that beat the going price for the house a buyer describes, and
proves each one from its source page.

## Language

### The buyer's side

**Brief**:
The house a buyer is looking for: an Area, size ranges, bedrooms and a budget.
_Avoid_: spec, query, search, filter, prompt, criteria

**Dashboard**:
The buyer's public website, hosted on AWS, where they define Jobs and read the Listing list for one Job. It never serves Snapshots or contact details from listing pages.
_Avoid_: console, admin, control panel

**Job**:
A buyer's saved hunt: one Brief, Portals chosen from a predefined list, and a daily time in Asia/Jakarta (plus Run now). Each firing is a Run. Any Brief change is a new Job, after a warning; the old Job keeps its list.
_Avoid_: task, campaign, alert, subscription

**Headroom**:
How far above the Brief's budget an asking price may be and still be shown, because asking prices are negotiable. A Listing shown this way is marked as over budget.
_Avoid_: tolerance, buffer, stretch

**Shortlist**:
The ranked Deals returned for one Brief.
_Avoid_: results, leaderboard, top deals

**Dossier**:
The evidence for one shortlisted Listing: its confirmed attributes, the Comps used and its Valuation.
_Avoid_: report card, detail page

### Listings

**Listing**:
One advertisement for a house on a Portal.
_Avoid_: property, ad, row, item

**Portal**:
A website that publishes Listings. The buyer picks from a predefined list on the Job; they do not type arbitrary domains.
_Avoid_: source, site, website

**Snapshot**:
The saved copy of a Listing's page at the moment it was fetched. Every claim cites one. Snapshots stay on the instance disk; they are not shown on the Dashboard.
_Avoid_: cache, raw page, scrape

**Listing Record**:
What DealScout believes a Listing says: price, land size, building size, bedrooms and the rest, each tied to the text it was read from.
_Avoid_: extraction, parsed row

**Readiness**:
Whether the house exists yet: Ready, or Indent when it is sold before it is built. An Indent Listing is never a Comp for a Ready one.
_Avoid_: status, condition, siap huni

**Duplicate**:
Two Listings that advertise the same house.
_Avoid_: repost

**Area**:
The named neighbourhood group that Comps are drawn from. Every Listing belongs to exactly one. The buyer may type it; DealScout maps that text to one canonical Area when it can. Unmapped text cannot draw Comps.
_Avoid_: location, region, district

### Trust

**Extraction Check**:
A test that one part of a Listing Record matches its Snapshot.
_Avoid_: flag, validation, vet

**Disagreement**:
The Scout and the Verifier read different values from the same Snapshot.
_Avoid_: conflict, mismatch

**Confirmed**:
A Listing Record that passed every Extraction Check and that the Verifier agreed with.
_Avoid_: verified, clean, valid

**Quarantined**:
A Listing Record that could not be Confirmed. It is reported with the reason and is never ranked or used as a Comp.
_Avoid_: fake, suspicious, rejected, dropped

**Unreachable**:
A Listing whose page could not be read.
_Avoid_: blocked, failed, dead

### Price

**Comp**:
A Confirmed Listing Record in the same Area and of similar size, used to price another.
_Avoid_: comparable, sample

**Market Price**:
The median asking price per square metre among a Listing's Comps, for land and for building. It reflects what sellers ask, not what houses sold for.
_Avoid_: fair value, median, benchmark

**Valuation**:
Where a Listing's asking price sits against Market Price: Below Market, At Market or Above Market. When there are fewer than three Comps, there is no ratio to show.
_Avoid_: verdict, tag, grade, undervalued, overpriced, score

**Split**:
A Valuation where land and building point in opposite directions.
_Avoid_: conflict, mixed

**Deal**:
A Confirmed Listing that fits the Brief and is Below Market.
_Avoid_: bargain, undervalue

### Running

**Run**:
One unattended execution of a Job, from plan to Shortlist.

**Scout**:
The agent that collects Listings and writes Listing Records.

**Verifier**:
The agent that re-reads a Snapshot on its own and judges a Listing Record without seeing the Scout's reasoning.

**Arbiter**:
The agent that settles a Disagreement.
