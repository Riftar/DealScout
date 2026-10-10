# DealScout design

How DealScout looks in public: posters for X, demo title cards, and the report when it is
styled. `CONTEXT.md` governs the words; this file governs the look.

Status: drafted by an agent on Sat 10 Oct 2026 from the posters the builder reviewed that
day. The builder owns this file. Until the builder approves it, work made from it is a draft.

## Identity

DealScout checks house listings against their own pages and shows which ones are priced
below market. The design should feel like a plain, careful notice: one claim, one number,
and where the number came from.

- Audience: people looking for a house in Indonesia, and the neatHack judges. Both meet the
  work in a feed and give it about two seconds.
- Personality: plain, exact, a little blunt. It states a fact and shows the source.
- It is not: a property brochure, a luxury brand, or a tech demo with glowing effects.

Dial: ENERGY 2 / RHYTHM 2 / MOTION 1.

## Colour

Two neutrals and one accent. Nothing else.

| Token | Light poster | Dark poster | Used for |
|---|---|---|---|
| `--paper` | `#f2ede2` | `#14130e` | Background |
| `--ink` | `#16150f` | `#f2ede2` | Headline, numbers, wordmark |
| `--muted` | `#6b6658` | `#a39c8a` | Supporting line, source note |
| `--rule` | `#cfc7b4` | `#3a372d` | Hairlines only, never text |
| `--accent` | `#c23620` | `#f0603f` | The one phrase or number the eye should land on |

Measured contrast against the background:

| Pair | Light | Dark |
|---|---|---|
| ink | 15.7:1 | 15.9:1 |
| muted | 4.9:1 | 6.8:1 |
| accent | 4.7:1 | 5.7:1 |

- The warm paper background is the motif that ties the set together. It reads as a printed
  notice, which suits adverts and prices.
- The accent appears once per piece, on the key phrase or number, plus the second half of
  the wordmark. A red dot may repeat it in a chart when the dots are the data.
- Light is the default. A dark piece is allowed for a single statistic that should stand
  apart from the pieces around it in the feed. One dark piece per set of three at most.
- No gradients, glows, shadows or background patterns.

## Type

| Role | Font | Weight | Size on a 1600 x 900 canvas |
|---|---|---|---|
| Headline | Bricolage Grotesque | 700 | 66 to 104 px, line height 1.02, tracking -0.03em |
| Hero number | Bricolage Grotesque | 800 | 200 to 210 px, tracking -0.03em |
| Supporting line | Bricolage Grotesque | 500 | 34 to 38 px, line height 1.3 |
| Wordmark | Bricolage Grotesque | 800 | 40 px |
| Source note, labels | IBM Plex Mono | 400 | 22 to 26 px |

- Bricolage Grotesque is a sans that reads at feed size and has its own letter shapes (the
  "y", "g" and "k"). The builder picked it on 10 Oct over Young Serif and Barlow Condensed.
  Two earlier tries were dropped: Fraunces, a high-contrast serif, was hard to read, and
  Archivo, a plain sans, looked generic.
- IBM Plex Mono is for the source note and the small labels under a number, so they read as
  a record. It is never used for a headline or a sentence the reader must take in first.
- Upright only. No italics, no all-caps, no wide letter spacing.
- Nothing below 22 px on a 1600 px canvas. A phone shows the poster at about a quarter of
  that width.
- Break headline lines by hand so no line ends on a single stranded word.

## Layout

Canvas for an X post: 1600 x 900 px, padding 60 px top, 88 px sides, 52 px bottom.

Three bands, top to bottom:

1. Header: the wordmark on the left, the status line on the right ("In build at #neatHack,
   10 to 12 Oct 2026"), with a 2 px ink rule under it.
2. Body: the message, vertically centred and left-aligned.
3. Footer: one note under a 1 px hairline rule. It says where the number came from, or what
   a key word in the headline means.

Body rules:

- One focal point: the hero number if there is one, otherwise the headline.
- At most three things in the body: headline, one picture or number, one supporting line.
- The picture is made from the data itself: two numbers side by side, or a grid of dots.
  There are no icons, illustrations, stock photos or screenshots of fake screens.
- Whitespace does the separating. There are no cards, boxes, badges or stamps.

## Wordmark

"DealScout" set in Bricolage Grotesque 800, with "Deal" in ink and "Scout" in the accent. There is no
logo or icon. If one is ever wanted, the builder supplies or approves it.

## Words on a poster

- A reader should get the point from the headline alone. Aim for 12 words or fewer.
- Plain words a house buyer uses: house, listing, price, size, below market, listing page.
  The agent names in `CONTEXT.md` (Scout, Verifier, Arbiter) and words like Snapshot stay
  out of headlines.
- Every number comes from `evidence/` or `hackathon.md`, and the footer says what it counts.
- State what exists. While a feature is unbuilt, the header says "In build".
- No person's name on a poster, and no repo link, because the link contains a name. The
  link goes in a reply under the post.
- No em dashes, no emoji, no exclamation marks.

## Motion

None. Posters are still images. In the demo video, cuts are plain and nothing loops.

## Where it lives

- `content/posters/poster.css` holds these tokens. Change this file first, then the CSS.
- `bash content/posters/render.sh` renders each poster page to a PNG with headless Edge.
- Posters, captions and scripts under `content/` are committed only after the builder
  approves them (`AGENTS.md`, "Done").

## Check before showing a poster

- The headline reads in two seconds at phone size.
- One accent, one focal point, at most three things in the body.
- Every number has a source, and the footer names it.
- Text meets 4.5:1 contrast; nothing is below 22 px.
- No name, no link, no claim about a feature that does not exist yet.
