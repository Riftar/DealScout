"""The Dashboard's pages as plain HTML. Look follows DESIGN.md: paper, ink, one accent."""

from __future__ import annotations

import html
from datetime import datetime

from dealscout.dashboard.schedule import JAKARTA
from dealscout.domain import (
    AREAS,
    JOB_PORTALS,
    Brief,
    Job,
    JobRun,
    JobRunState,
    ListingList,
    ListingRow,
    RunTrigger,
    ValuationTier,
)

_TIER_WORDS = {
    ValuationTier.BELOW_MARKET: "Below Market",
    ValuationTier.AT_MARKET: "At Market",
    ValuationTier.ABOVE_MARKET: "Above Market",
}
_STATE_WORDS = {
    JobRunState.QUEUED: "waiting to start",
    JobRunState.RUNNING: "going now",
    JobRunState.DONE: "finished",
    JobRunState.FAILED: "failed",
}


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def rupiah(value: float | None) -> str:
    if value is None:
        return "not stated"
    return "Rp " + f"{round(value):,}".replace(",", ".")


def when(moment: datetime | None) -> str:
    if moment is None:
        return ""
    return moment.astimezone(JAKARTA).strftime("%d %b %Y, %H:%M WIB")


def _size(value: float | None) -> str:
    return f"{value:g} m²" if value is not None else "?"


def brief_line(brief: Brief) -> str:
    parts = [f"budget {rupiah(brief.budget_rp)}", f"Headroom {brief.headroom:.0%}"]
    if brief.land_m2:
        parts.append(f"land {brief.land_m2:g} m²")
    if brief.building_m2:
        parts.append(f"building {brief.building_m2:g} m²")
    if brief.bedrooms is not None:
        parts.append(f"{brief.bedrooms} bedrooms")
    return " · ".join(parts)


def portal_names(portals: list[str]) -> str:
    return ", ".join(JOB_PORTALS.get(name, name) for name in portals)


def page(title: str, body: str, *, refresh: int | None = None) -> str:
    meta = f'<meta http-equiv="refresh" content="{refresh}">\n' if refresh else ""
    return (
        "<!doctype html>\n"
        '<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"{meta}<title>{esc(title)} · DealScout</title>\n"
        '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
        'family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,700;12..96,800'
        '&family=IBM+Plex+Mono&display=swap">\n'
        f"<style>{_CSS}</style>\n</head>\n<body>\n"
        '<header class="top"><a class="wordmark" href="/">Deal<span>Scout</span></a>'
        '<a class="nav" href="/jobs/new">Define a Job</a></header>\n'
        f"<main>\n{body}\n</main>\n"
        '<footer class="note">Market Price is the median asking price per square metre among a '
        "Listing's Comps. It reflects what sellers ask, not what houses sold for.</footer>\n"
        "</body>\n</html>\n"
    )


# Home


def home(jobs: list[Job], last_runs: dict[int, JobRun | None]) -> str:
    if not jobs:
        rows = (
            '<p class="empty">No Jobs yet. <a href="/jobs/new">Define a Job</a> to describe the '
            "house and pick when DealScout looks for it each day.</p>"
        )
    else:
        body = "".join(_job_row(job, last_runs.get(job.id)) for job in jobs)
        rows = (
            '<div class="scroll"><table><thead><tr><th>Job</th><th>Brief</th><th>Portals</th>'
            "<th>Daily Run</th><th>Latest Run</th></tr></thead>"
            f"<tbody>{body}</tbody></table></div>"
        )
    return page(
        "Jobs",
        "<h1>Listings priced below market, checked against their own pages.</h1>\n"
        '<p class="lede">A Job is one house you describe, the Portals to read, and a time of day. '
        "DealScout runs it every day and keeps the Listing list here.</p>\n"
        f"<h2>Jobs</h2>\n{rows}",
    )


def _job_row(job: Job, last: JobRun | None) -> str:
    latest = f"{_STATE_WORDS[last.state]}, {when(last.finished_at or last.queued_at)}" if last else "none yet"
    daily = f"{job.daily_time} WIB" if job.active else "stopped"
    return (
        f'<tr><td><a href="/jobs/{job.id}">{esc(job.brief.area)}</a></td>'
        f'<td class="mono">{esc(brief_line(job.brief))}</td>'
        f"<td>{esc(portal_names(job.portals))}</td>"
        f'<td class="mono">{esc(daily)}</td><td>{esc(latest)}</td></tr>'
    )


# Job form


def job_form(
    values: dict[str, object],
    errors: dict[str, str],
    *,
    action: str,
    editing: Job | None = None,
) -> str:
    def field(name: str, label: str, hint: str = "", **attrs: str) -> str:
        extra = "".join(f' {key.rstrip("_")}="{esc(val)}"' for key, val in attrs.items())
        error = f'<p class="error" id="{name}-error">{esc(errors[name])}</p>' if name in errors else ""
        described = f' aria-describedby="{name}-error"' if name in errors else ""
        hint_html = f'<span class="hint">{esc(hint)}</span>' if hint else ""
        return (
            f'<label for="{name}">{esc(label)}{hint_html}</label>'
            f'<input id="{name}" name="{name}" value="{esc(values.get(name, ""))}"{extra}{described}>'
            f"{error}"
        )

    headroom = str(values.get("headroom", "5"))
    headroom_options = "".join(
        f'<option value="{pct}"{" selected" if str(pct) == headroom else ""}>{pct}%</option>'
        for pct in range(0, 11)
    )
    chosen = values.get("portals") or []
    portal_boxes = "".join(
        f'<label class="check"><input type="checkbox" name="portals" value="{esc(name)}"'
        f'{" checked" if name in chosen else ""}> {esc(label)}</label>'
        for name, label in JOB_PORTALS.items()
    )
    portal_error = f'<p class="error">{esc(errors["portals"])}</p>' if "portals" in errors else ""
    areas = "".join(f'<option value="{esc(area)}">' for area in AREAS)
    if editing is None:
        heading, lede, button = (
            "Define a Job",
            "Describe the house. DealScout looks for it once a day at the time you pick.",
            "Save the Job",
        )
    else:
        heading, lede, button = (
            f"Change the Job for {editing.brief.area}",
            "Portals and the daily time change this Job. A change to the house itself makes a "
            "new Job, and this one keeps its Listing list.",
            "Save",
        )
    return page(
        heading,
        f"<h1>{esc(heading)}</h1>\n<p class=\"lede\">{esc(lede)}</p>\n"
        f'<form method="post" action="{esc(action)}">\n'
        "<fieldset><legend>The house</legend>\n"
        + field("area", "Area", "A neighbourhood, for example Bintaro or BSD", list_="areas", required="", maxlength="60")
        + f'<datalist id="areas">{areas}</datalist>'
        + field("budget", "Budget", "In Rupiah: 1500000000, 850 juta or 1,5 miliar", required="", inputmode="text", maxlength="30")
        + f'<label for="headroom">Headroom<span class="hint">How far above budget an asking '
        f'price may be and still be shown</span></label><select id="headroom" name="headroom">{headroom_options}</select>'
        + field("land_m2", "Land size in m²", "Optional", inputmode="decimal", maxlength="8")
        + field("building_m2", "Building size in m²", "Optional", inputmode="decimal", maxlength="8")
        + field("bedrooms", "Bedrooms", "Optional", inputmode="numeric", maxlength="2")
        + "</fieldset>\n<fieldset><legend>Where and when</legend>\n"
        f'<p class="label">Portals</p><div class="checks">{portal_boxes}</div>{portal_error}'
        + field("daily_time", "Daily Run at", "Asia/Jakarta time", type="time", required="")
        + f'</fieldset>\n<button type="submit">{esc(button)}</button>\n</form>',
    )


def confirm_new_job(old: Job, new_brief: Brief, hidden: dict[str, list[str]]) -> str:
    fields = "".join(
        f'<input type="hidden" name="{esc(name)}" value="{esc(value)}">'
        for name, values in hidden.items()
        for value in values
    )
    return page(
        "A new Job",
        "<h1>This change makes a new Job.</h1>\n"
        '<p class="lede">The house you describe is what a Listing list is built on, so a '
        "different house gets its own Job. The Job you have now keeps its Listing list and "
        "stops its daily Runs.</p>\n"
        f'<p class="mono">Now: {esc(old.brief.area)} · {esc(brief_line(old.brief))}</p>\n'
        f'<p class="mono">New: {esc(new_brief.area)} · {esc(brief_line(new_brief))}</p>\n'
        f'<form method="post" action="/jobs/{old.id}">{fields}'
        '<input type="hidden" name="confirm" value="1">'
        '<button type="submit">Make the new Job</button> '
        f'<a class="quiet" href="/jobs/{old.id}">Keep this Job as it is</a></form>',
    )


# One Job


def job_page(
    job: Job,
    runs: list[JobRun],
    shown: JobRun | None,
    *,
    replaced_by: int | None = None,
    notice: str | None = None,
) -> str:
    open_run = next((r for r in runs if r.state in (JobRunState.QUEUED, JobRunState.RUNNING)), None)
    parts = [f"<h1>{esc(job.brief.area)}, up to {esc(rupiah(job.brief.budget_rp))}</h1>"]
    parts.append(f'<p class="mono">Brief: {esc(brief_line(job.brief))}</p>')
    if job.active:
        schedule = f"runs every day at {job.daily_time} WIB"
    elif replaced_by:
        schedule = f'stopped; <a href="/jobs/{replaced_by}">a newer Job</a> replaced it'
    else:
        schedule = "daily Runs are stopped"
    parts.append(f'<p class="mono">Portals: {esc(portal_names(job.portals))} · {schedule}</p>')
    if not job.area_mapped:
        parts.append(
            f'<p class="warn">DealScout does not know "{esc(job.area_text)}" as an Area, so it '
            "cannot draw Comps for it. Listings are matched on their location text and shown "
            "without a Valuation.</p>"
        )
    if notice:
        parts.append(f'<p class="warn" role="status">{esc(notice)}</p>')
    if open_run is not None:
        parts.append(
            f'<p class="status" role="status">A Run is {_STATE_WORDS[open_run.state]}. '
            "This page reloads until it finishes.</p>"
        )
    toggle = "Stop daily Runs" if job.active else "Resume daily Runs"
    parts.append(
        '<div class="actions">'
        f'<form method="post" action="/jobs/{job.id}/run"><button type="submit"'
        f'{" disabled" if open_run else ""}>Run now</button></form>'
        f'<a class="quiet" href="/jobs/{job.id}/edit">Change the Job</a>'
        f'<form method="post" action="/jobs/{job.id}/active">'
        f'<input type="hidden" name="active" value="{0 if job.active else 1}">'
        f'<button type="submit" class="plain">{toggle}</button></form></div>'
    )
    if shown is not None and shown.listing_list is not None:
        parts.append(_listing_list(shown, shown.listing_list))
    elif not runs:
        parts.append('<p class="empty">No Run yet. The first Listing list appears after one.</p>')
    if runs:
        parts.append(_run_history(job, runs, shown))
    return page(
        f"{job.brief.area} Job",
        "\n".join(parts),
        refresh=20 if open_run is not None else None,
    )


def _listing_list(run: JobRun, found: ListingList) -> str:
    deals = sum(1 for row in found.rows if row.is_deal)
    if found.comp_count:
        market = (
            f"Market Price from {found.comp_count} Comps: "
            f"{rupiah(found.market_rp_per_land_m2)} per m² of land, "
            f"{rupiah(found.market_rp_per_building_m2)} per m² of building."
        )
    else:
        market = "Fewer than three Comps, so there is no Valuation ratio to show."
    out = [
        f"<h2>Listing list</h2>\n<p class=\"mono\">Run finished {esc(when(run.finished_at))} · "
        f"{len(found.rows)} fit the Brief · {deals} Below Market · {found.confirmed} Confirmed · "
        f"{len(found.quarantined)} Quarantined · {len(found.unreachable)} Unreachable</p>\n"
        f"<p>{esc(market)}</p>"
    ]
    if found.rows:
        body = "".join(_listing_row(row) for row in found.rows)
        out.append(
            '<div class="scroll"><table><thead><tr><th>Listing</th><th class="num">Asking price</th>'
            '<th>Land / building</th><th>Bedrooms / bathrooms</th><th>Readiness</th>'
            f"<th>Valuation</th></tr></thead><tbody>{body}</tbody></table></div>"
        )
    else:
        out.append('<p class="empty">No Confirmed Listing fits the Brief in this Run.</p>')
    aside = []
    if found.outside_brief:
        aside.append(f"{found.outside_brief} Confirmed outside the Brief")
    if found.duplicates:
        aside.append(f"{found.duplicates} Duplicates left out")
    if aside:
        out.append(f'<p class="mono">{esc(" · ".join(aside))}</p>')
    for title, held in (("Quarantined", found.quarantined), ("Unreachable", found.unreachable)):
        if held:
            body = "".join(
                f"<tr><td>{_listing_link(row)}</td><td>{esc(row.reason or '')}</td></tr>" for row in held
            )
            out.append(
                f'<h3>{title}</h3>\n<div class="scroll"><table><thead><tr><th>Listing</th>'
                f"<th>Reason</th></tr></thead><tbody>{body}</tbody></table></div>"
            )
    return "\n".join(out)


def _listing_link(row: ListingRow) -> str:
    label = JOB_PORTALS.get(row.portal, row.portal)
    if row.listing_id:
        label += f" {row.listing_id}"
    if not row.url.startswith(("https://", "http://")):
        return esc(label)
    return f'<a href="{esc(row.url)}" rel="noopener noreferrer">{esc(label)}</a>'


def _listing_row(row: ListingRow) -> str:
    price = esc(rupiah(row.price_rp))
    if row.over_budget:
        price += '<span class="sub">over budget</span>'
    if row.ratio is None or row.tier is None:
        valuation = '<span class="sub">no ratio</span>'
    else:
        css = ' class="deal"' if row.is_deal else ""
        valuation = f"<span{css}>{_TIER_WORDS[row.tier]}</span> <span class=\"mono\">{row.ratio:.2f}</span>"
        if row.split:
            valuation += '<span class="sub">Split: land and building disagree</span>'
    rooms = f"{row.bedrooms if row.bedrooms is not None else '?'} / {row.bathrooms if row.bathrooms is not None else '?'}"
    misses = f'<span class="sub">off the Brief: {esc(", ".join(row.soft_misses))}</span>' if row.soft_misses else ""
    return (
        f"<tr><td>{_listing_link(row)}{misses}</td>"
        f'<td class="num">{price}</td>'
        f"<td>{esc(_size(row.land_m2))} / {esc(_size(row.building_m2))}</td>"
        f"<td>{esc(rooms)}</td>"
        f"<td>{esc(row.readiness.value.capitalize() if row.readiness else '?')}</td>"
        f"<td>{valuation}</td></tr>"
    )


def _run_history(job: Job, runs: list[JobRun], shown: JobRun | None) -> str:
    items = []
    for run in runs:
        trigger = "daily" if run.trigger is RunTrigger.DAILY else "Run now"
        text = f"{when(run.finished_at or run.started_at or run.queued_at)} · {trigger} · {_STATE_WORDS[run.state]}"
        if run.error:
            text += f": {run.error}"
        if run.state is JobRunState.DONE and (shown is None or run.id != shown.id):
            items.append(f'<li><a href="/jobs/{job.id}?run={run.id}">{esc(text)}</a></li>')
        else:
            current = " (shown above)" if shown is not None and run.id == shown.id else ""
            items.append(f"<li>{esc(text)}{current}</li>")
    return f'<h2>Runs</h2>\n<ul class="runs mono">{"".join(items)}</ul>'


def message(title: str, text: str) -> str:
    return page(title, f'<h1>{esc(title)}</h1>\n<p class="lede">{esc(text)}</p>\n<p><a href="/">Back to Jobs</a></p>')


_CSS = """
:root { --paper:#f2ede2; --ink:#16150f; --muted:#6b6658; --rule:#cfc7b4; --accent:#c23620; }
@media (prefers-color-scheme: dark) {
  :root { --paper:#14130e; --ink:#f2ede2; --muted:#a39c8a; --rule:#3a372d; --accent:#f0603f; }
}
* { box-sizing: border-box; }
body { margin: 0 auto; max-width: 68rem; padding: 1.5rem 1rem 3rem; background: var(--paper);
  color: var(--ink); font: 500 1.0625rem/1.5 "Bricolage Grotesque", "Segoe UI", system-ui, sans-serif; }
.top { display: flex; justify-content: space-between; align-items: baseline; gap: 1rem;
  border-bottom: 2px solid var(--ink); padding-bottom: 0.75rem; }
.wordmark { font-weight: 800; font-size: 1.5rem; color: var(--ink); text-decoration: none; letter-spacing: -0.02em; }
.wordmark span { color: var(--accent); }
a { color: var(--ink); text-underline-offset: 0.18em; }
a:hover { color: var(--accent); }
:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
h1 { font-size: clamp(1.9rem, 5vw, 3rem); line-height: 1.05; letter-spacing: -0.03em; font-weight: 700;
  margin: 2rem 0 0.75rem; max-width: 22ch; text-wrap: balance; }
h2 { font-size: 1.35rem; font-weight: 700; letter-spacing: -0.01em; margin: 2.5rem 0 0.5rem; }
h3 { font-size: 1.05rem; font-weight: 700; margin: 2rem 0 0.25rem; }
.lede { font-size: 1.2rem; line-height: 1.35; max-width: 46ch; margin: 0 0 1rem; }
.mono, .note, .hint, .sub, th { font-family: "IBM Plex Mono", ui-monospace, Consolas, monospace;
  font-weight: 400; font-size: 0.82rem; }
.mono, .note, .hint, .sub, .empty { color: var(--muted); }
.mono { margin: 0.25rem 0; }
td .mono { margin: 0; }
.sub { display: block; }
.scroll { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; margin-top: 0.5rem; }
th, td { text-align: left; vertical-align: top; padding: 0.6rem 1rem 0.6rem 0; border-bottom: 1px solid var(--rule); }
th { color: var(--muted); border-bottom-color: var(--ink); white-space: nowrap; }
.num { text-align: right; white-space: nowrap; font-variant-numeric: tabular-nums; }
.deal { color: var(--accent); font-weight: 700; }
.warn, .status { border-top: 1px solid var(--rule); border-bottom: 1px solid var(--rule); padding: 0.6rem 0; max-width: 60ch; }
.error { color: var(--accent); margin: 0.25rem 0 0; font-size: 0.95rem; }
.actions { display: flex; flex-wrap: wrap; align-items: center; gap: 0.75rem 1.5rem; margin: 1.25rem 0; }
form { margin: 0; }
fieldset { border: 0; border-top: 1px solid var(--rule); padding: 0.5rem 0 0; margin: 1.5rem 0 0; max-width: 34rem; }
legend { font-weight: 700; padding: 0 0.5rem 0 0; }
label, .label { display: block; margin: 1rem 0 0.25rem; font-weight: 700; }
.hint { display: block; }
input:not([type=checkbox]), select { width: 100%; min-height: 2.75rem; padding: 0.5rem 0.6rem; font: inherit;
  color: var(--ink); background: transparent; border: 1px solid var(--ink); border-radius: 0; }
.checks { display: flex; flex-wrap: wrap; gap: 0.25rem 1.25rem; }
.check { font-weight: 500; margin: 0; min-height: 2.75rem; display: flex; align-items: center; gap: 0.4rem; }
button { min-height: 2.75rem; padding: 0.5rem 1.1rem; font: inherit; font-weight: 700; cursor: pointer;
  color: var(--paper); background: var(--ink); border: 1px solid var(--ink); border-radius: 0; }
button:hover { background: var(--accent); border-color: var(--accent); }
button[disabled] { opacity: 0.45; cursor: default; }
button.plain { color: var(--ink); background: transparent; }
button.plain:hover { color: var(--accent); background: transparent; }
form > button { margin-top: 1.5rem; }
.actions form > button { margin-top: 0; }
.runs { list-style: none; padding: 0; margin: 0.5rem 0 0; }
.runs li { padding: 0.35rem 0; border-bottom: 1px solid var(--rule); }
.note { border-top: 1px solid var(--rule); margin-top: 3rem; padding-top: 0.75rem; max-width: 70ch; }
"""
