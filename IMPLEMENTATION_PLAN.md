# Anaheim Travel Guide App — Implementation Plan

## Goal
Convert the existing EN-VI Translator app into a mobile-first curated travel guide for ADLM 2026 in Anaheim, CA. Purpose: help the user and colleague navigate from airport to conference venue, find hotels, food, and activities — all offline-capable via service worker.

## User Context
- Fly from Vietnam, arrive July 24 or 25, 2026
- Attending ADLM 2026 (Association for Diagnostic Laboratory Medicine)
- Poster presentation on Expo Show floor, Poster hall
- Budget: ~$50/day for 2 people
- No US driving experience, no US SIM/roaming
- Phone has internet connection
- First time to USA
- Language: English UI

## Research Findings
- ADLM 2026: July 26–30, 2026 at Anaheim Convention Center (800 W Katella Ave)
- SNA (John Wayne Airport) is ~15-20 min from Anaheim — preferred over LAX
- LAX is ~45-60 min from Anaheim
- Expo dates: July 28–30
- Opening Mixer: Sunday July 26, 6:30–8:00 PM

## Architecture
- Flask backend serving curated JSON data
- Single-page mobile frontend (HTML/CSS/JS)
- Service worker for offline caching
- Google Maps embedded directions via iframe
- No AI model needed — all static curated data

## Pages/Routes
1. Trip Overview — dates, venue, key contacts
2. Airport Arrival — SNA vs LAX comparison, customs tips
3. Transport — Uber/Lyft, shuttle, public transit with costs
4. Hotel — recommendations near convention center
5. Conference — ADLM schedule, floor plan link, poster info
6. Food & Dining — budget options near venue
7. Maps & Directions — embedded Google Maps
8. Emergency — contacts, embassy, medical

## Backend Endpoints
- `GET /api/airport` — airport arrival data
- `GET /api/transport` — transport options with costs
- `GET /api/hotels` — hotel list
- `GET /api/schedule` — ADLM schedule
- `GET /api/food` — restaurant list
- `GET /api/emergency` — emergency contacts

## Offline Strategy
- Service worker caches all static assets + API JSON on first load
- Network-first for API calls, fallback to cached data
- Google Maps iframes show placeholder when offline

## Budget Breakdown (per day for 2 people)
- Accommodation: ~$120-150/night (split = $60-75/each)
- Transport: $10-20/day shared
- Food: $40-60/day for 2 people
- Total: ~$50-70/day each realistic
- Note: hotel is the single biggest cost — staying near venue saves transport

## File Changes
- Overwrite `app.py` with new guide endpoints
- Overwrite `static/index.html` with new SPA
- Overwrite `static/manifest.json` with new app details
- Overwrite `static/sw.js` for offline caching
- Remove translation-specific code
- Keep `.env`, `requirements.txt` (Flask deps only)

## Testing
1. Start Flask on WSL
2. Open tunnel via LocalTunnel
3. Test from phone browser
4. Verify offline mode by turning off WiFi
