# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Primary: tender-drafting and procurement officials at Indian government bodies (CPWD, GeM, state PWDs, PSUs, and similar) who know what they need to buy in plain or trade language but not which Bureau of Indian Standards (IS) code covers it. Confirmed by the underlying data model (CPWD DSR / GeM / MoRTH schedule matching, QCO/certification enforcement) and by the official SIH problem-statement text (below).

## Product Purpose

Built for Smart India Hackathon 2026, Problem Statement 26108 (Department of Consumer Affairs / Bureau of Indian Standards): an AI-powered recommendation engine that takes a product description, technical specification, or full tender document and recommends the applicable Indian Standard(s) by semantic understanding rather than keyword matching; identifies allied standards (normative references, test methods, safety, installation, related-product); flags mandatory certification requirements (ISI Mark, CRS, Hallmarking) under BIS Quality Control Orders; and supports multilingual/natural-language input.

## Positioning

Distinct from a keyword search of a standards catalogue: hybrid dense + lexical retrieval with cross-encoder reranking, backed by a locally-embedded 33,564-standard registry, live-sourced QCO/certification data, and an explicit confidence/provenance layer that tells the officer how much to trust a given answer rather than presenting every result as equally authoritative.

## Operating Context

An officer pastes a product description, a line from a Bill of Quantities, or uploads a tender PDF/CSV. The tool returns ranked IS codes with a confidence band, certification flags, allied standards, and edition state; for tenders, it audits each line item against a four-state verdict (COMPLIANT / QCO_REQUIRED / STANDARD_SUGGESTED / NO_CONFIDENT_MATCH); a separate tool drafts GeM-ready clause text for a recommended standard. Runs fully offline once models are cached (CPU-only, no GPU assumed), so latency (measured ~1-10s per query on this hardware) and live-backend availability are real usage-scene constraints, not edge cases.

## Capabilities and Constraints

- Search (free text, and Hindi/Marathi/Tamil/Telugu/Bengali/Gujarati/Kannada/Hinglish input), tender/BoQ PDF and CSV audit, GeM clause generation, single-standard lookup.
- Confidence is real and must stay visually honest: HIGH (>=0.75) / MEDIUM (>=0.50) / LOW bands, driven by a single scoring function; `match_quality` of confident / uncertain / no_match per query.
- Provenance matters: registry snapshot date, edition state (`latest_in_registry` / `later_edition_exists` / `restructured_edition_exists` / `no_edition_data`), and superseded-standard warnings are real, measured signals -- the UI must not bury them or flatten them into a single generic "verified" checkmark.
- Multilingual OUTPUT is only real for 12 of 33,564 standards; everything else renders in English. The UI must not visually imply full translation coverage it doesn't have.
- QCO/certification coverage is ~1.7-2% of the registry; "voluntary" is a real possible (and sometimes wrong) answer, not just an empty state.
- No dummy, placeholder, or demo data anywhere in the shipped UI -- every example, chip, or sample result must be a real value the live backend actually returns.
- CPU-only inference is slow (cold first query ~10s; warm/repeated-query median ~1.1-3.3s) -- loading and pending states are a first-class part of the design, not an afterthought.
- Undated standards (40% of the registry) and generated, not extracted, scope text (98.2% of the registry) are real data-quality facts the UI already discloses in places; the redesign must not regress that disclosure.

## Brand Commitments

Current in-UI name: "Indian Standards Recommendation Platform" -- not yet a fixed brand asset, open to a sharper identity as part of this redesign. No existing logo beyond a text "IS" monogram. Official Government of India visual language (Ashoka emblem, tricolour framing) is not currently used and is an open creative decision for this redesign, not a locked commitment either way.

## Evidence on Hand

Real, live backend (FastAPI, `127.0.0.1:8000`) serving real data: 33,564 Indian Standards, 759 QCO/certification rules sourced from bis.gov.in and crsbis.in, 2,404 allied-standard edges, a 1,024-dim BGE-M3 dense index plus a BM25 lexical index. A full, dated, evidence-cited system audit exists at `docs/SYSTEM_ANALYSIS.md` -- treat it as ground truth for what the product can and cannot honestly claim. No fabricated testimonials, customers, or benchmark claims exist or should be introduced.

## Product Principles

1. Never claim more certainty than the data supports -- confidence bands, provenance, and known coverage gaps are core UI content, not fine print.
2. Every number, example, and result on screen comes from the live backend. No placeholder or demo data, ever.
3. The person using this is doing a job under real institutional stakes -- a wrong standard cited in a tender is a real procurement risk. Design for a professional completing a task with confidence, not for a consumer being delighted.
4. Slow, CPU-bound responses are a real constraint of the offline-first design -- make waiting legible and trustworthy rather than hiding or apologizing for it.
5. Multilingual input is a genuine differentiator; multilingual output is not yet. The UI must represent that asymmetry honestly.

## Accessibility & Inclusion

Multilingual by design (7 Indian languages plus English and Hinglish on the input side). The existing header already carries a "Skip to main content" link and an EN/हिन्दी toggle -- confirmed, real commitments to preserve.
