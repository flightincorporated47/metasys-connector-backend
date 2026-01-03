# Metasys Connector Polling Tier SOPs
**Document set:** Polling Tiers + Points Lists  
**Applies to:** Local Site Management UI + Connector Config JSON (v3)  
**Last updated:** 2026-01-01

These SOPs cover how to take a list of Metasys “Item Reference” strings (like `metasys02:NAE24-CSUDH/...`) and safely add them to the connector configuration under:

`connector.polling.tiers[].points`

---

## Key rule (the one that bites people)
✅ **Every point must be its own string in the JSON array.**

**Correct (each point is separate):**
```json
"points": [
  "metasys02:NAE24-CSUDH/FC-1.FEC-4.DA-T",
  "metasys02:NAE24-CSUDH/FC-1.FEC-4.DA-P"
]
```

❌ **Wrong (many points jammed into one giant string):**
```json
"points": [
  "metasys02:...DA-T metasys02:...DA-P metasys02:...DA-F"
]
```

If you paste them “space-separated” like the wrong example, the connector will treat that as **one** point reference and you’ll get errors / missing data.

---

## Where you paste in Site Management
1. Open the Site Management page (your local UI).
2. Select the project.
3. Click **Open Config**.
4. Scroll to: `connector → polling → tiers`.
5. Expand the tier you’re editing (fast / medium / slow).
6. Put your list inside the `"points": [ ... ]` array (again: one string per line).

---

## A safe copy/paste format
When you have a plain list (one per line), convert it to this “JSON list style” before pasting:

```json
"metasys02:NAE24-CSUDH/FC-1.FEC-4.DA-T",
"metasys02:NAE24-CSUDH/FC-1.FEC-4.DA-P",
"metasys02:NAE24-CSUDH/FC-1.FEC-4.DA-F"
```

Notes:
- Quotes **required**
- Comma at the end of every line **except** the last line (JSON rule)
- No trailing comma after the last item

---

## Before you start (pre-flight checklist)
- ✅ Backend API running (the thing listening on `http://127.0.0.1:8787/api/v1`)
- ✅ Frontend UI running (the thing you open at `http://localhost:8080/`)
- ✅ You can see **Projects (1)** and your project loads.
- ✅ You can click **Open Config** and see “Config loaded (v3)”.
- ✅ You have your Item Reference list ready (from Metasys Advanced Search export, etc.)

---

## After you save (verification checklist)
1. Click **Save Config**.
2. Confirm it says something like “Saved. Version: X”.
3. Click **Generate YAML** and confirm the YAML updates (tiers show your points).
4. Optional: click **YAML Diff** to confirm only the expected section changed.
5. If something breaks: revert by re-opening config and undoing changes, or restoring from a previous saved version (depending on how your backend stores versions).

---


# SOP: Fast Polling Setup (Use Carefully)

## Goal
High-resolution data for troubleshooting, commissioning, or short-term validation.

This mode is like espresso shots:
- Amazing for the right moment
- Terrible as your only hydration plan

## Recommended strategy (safe fast)
- Keep `slow` at **300s** for the majority of points
- Keep `medium` at **30s** for important points
- Put only a **small troubleshooting subset** into `fast`

### Suggested tier intervals (fast mode)
- `fast`: **5s** (recommend 5–25 points max)
- `medium`: **30s**
- `slow`: **300s**

If you *must* go faster than 5s, do it only temporarily and only with a handful of points.

### Suggested polling and publish settings
- `connector.polling.batch_size`: **100–200** (but start at 100)
- `connector.polling.default_deadband_pct`: **0.5–1%**
- `connector.delta_publishing.min_interval_ms`: **500–1000 ms** (start at 1000)

---

## Step-by-step (Fast)

### 1) Confirm baseline stability
Before enabling fast points:
1. Conservative or Medium config has been stable
2. No persistent errors in your logs/console
3. You know exactly which points need high resolution

### 2) Create your “fast list” (tiny subset)
Good fast candidates:
- A VFD speed reference or command
- A single key pressure used for control (DA-P)
- A valve command/position you are actively debugging
- A binary status you’re trying to correlate with alarms/faults

Bad fast candidates:
- Huge device lists
- Every AI/AV in the building
- “All points because storage is cheap” (Metasys is the one doing the cardio)

### 3) Paste fast list into `fast` tier
1. Find tier `"name": "fast"`
2. Paste the list as separate strings:
   ```json
   {
     "name": "fast",
     "interval_s": 5,
     "points": [
       "metasys02:NAE24-CSUDH/FC-1.FEC-4.DA-P",
       "metasys02:NAE24-CSUDH/FC-1.FEC-4.SF1-S"
     ]
   }
   ```

### 4) Remove those fast points from other tiers
A point should appear in **only one** tier.
- If you add it to fast, remove it from medium/slow.

### 5) Save and validate
1. Click **Save Config**
2. Click **Generate YAML**
3. Confirm tiers show what you expect
4. Watch behavior for a few minutes (UI responsiveness, error messages, etc.)

---

## Fast mode “exit strategy”
Fast mode should come with a planned end:
- After troubleshooting is done, move fast points back to medium or slow
- Save config again
- Generate YAML again
- Done. No lingering “why is this so chatty?” surprises later.

---

## Rollback plan (Fast)
If anything looks unhappy:
1. Empty the fast points array:
   ```json
   "points": []
   ```
2. Save config
3. Confirm medium/slow still contains your full list

