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


# SOP: Conservative Polling Setup (Recommended Baseline)

## Goal
Minimize risk to the Metasys server / network while still collecting useful trends.
This is the setup you use when:
- You’re piloting a new site/project
- You’re unsure how chatty the NAE/Metasys environment can be
- You want to avoid “why is everything slow?” calls from IT

## Recommended config posture
- **Use only the `slow` tier for most points**
- Leave `fast` and `medium` empty at first
- Only move points upward (slow → medium → fast) after you observe stable performance

### Suggested tier intervals
- `fast`: **5s** (keep points empty initially)
- `medium`: **30s** (keep points empty initially)
- `slow`: **300s** (5 minutes) **→ put your list here**

### Suggested polling and publish settings (safe defaults)
- `connector.polling.batch_size`: **50–100**
- `connector.polling.default_deadband_pct`: **1–2%**
- `connector.delta_publishing.min_interval_ms`: **1000–2000 ms**

You can keep your existing values if things are working; these ranges are simply “safe and boring.”

---

## Step-by-step (Conservative)

### 1) Open the project config
1. Go to `http://localhost:8080/`
2. Select your project (ex: **CSUDH Central Plant**)
3. Click **Open Config**
4. Confirm: **Config loaded (v3)**

### 2) Put everything into the `slow` tier
1. Find:
   - `connector`
   - `polling`
   - `tiers`
2. Locate the object where `"name": "slow"`
3. Ensure it looks like:
   ```json
   {
     "name": "slow",
     "interval_s": 300,
     "points": [ ]
   }
   ```
4. Paste your points list into that `points` array, **one string per line**:
   ```json
   "points": [
     "metasys02:NAE24-CSUDH/FC-1.FEC-4.DA-T",
     "metasys02:NAE24-CSUDH/FC-1.FEC-4.DA-P"
   ]
   ```

### 3) Save config
1. Click **Save Config**
2. If you get an error:
   - It’s usually JSON formatting (missing comma, missing quote, etc.)
   - The error message will tell you roughly where

### 4) Validate output
1. Click **Generate YAML**
2. Confirm:
   - Your points appear under the `slow` tier
3. (Optional) Click **YAML Diff** to see what changed

---

## Conservative tuning guidance (when to move off “slow”)
Move a point to **medium** only if:
- You truly need faster response than 5 minutes, **and**
- You’ve observed stable operation for at least a day or two

Examples that can justify **medium (30s)**:
- Space temperature / humidity in a critical zone
- Differential pressure that’s part of an active control sequence
- A VFD speed reference if you’re validating control behavior

Keep **fast (5s)** for:
- Very small, critical subsets (a handful of points)
- Short-term troubleshooting sessions, not “forever mode”

---

## Rollback plan (Conservative)
If you see issues (timeouts, errors, missing data):
1. Move everything back to **slow**
2. Reduce `batch_size` to **50**
3. Save config again
4. Re-test with **Generate YAML**

