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


# SOP: Medium Polling Setup (Balanced)

## Goal
Collect most data at a comfortable cadence while keeping the network/NAE load reasonable.

Use this after Conservative has been stable and you want:
- Better trending fidelity (more points per minute)
- Moderate responsiveness for important points

## Recommended strategy
- **Most points stay in `slow` (300s)**
- Put a limited “important subset” into `medium` (30s)
- Keep `fast` either empty or very small

### Suggested tier intervals
- `fast`: **5s** (0–10 points max, optional)
- `medium`: **30s** (important points)
- `slow`: **300s** (everything else)

### Suggested polling and publish settings
- `connector.polling.batch_size`: **100**
- `connector.polling.default_deadband_pct`: **1%**
- `connector.delta_publishing.min_interval_ms`: **1000 ms**

---

## Step-by-step (Medium)

### 1) Start from the Conservative config
1. Open the project
2. Click **Open Config**
3. Confirm config loads cleanly

### 2) Build your “medium list” (important subset)
Pick points that benefit from 30-second resolution, such as:
- Supply fan status, VFD ref/speed
- Key temperatures (MA-T, DA-T, OA-T) and key pressures (DA-P)
- Any value you use for control validation / fault detection

**Do NOT put everything in medium**. Medium is for “the story of what happened,” not “every syllable.”

### 3) Paste points into `medium`
1. Find tier where `"name": "medium"`
2. Paste the subset into `points`
3. Example:
   ```json
   {
     "name": "medium",
     "interval_s": 30,
     "points": [
       "metasys02:NAE24-CSUDH/FC-1.FEC-4.DA-T",
       "metasys02:NAE24-CSUDH/FC-1.FEC-4.DA-P",
       "metasys02:NAE24-CSUDH/FC-1.FEC-4.MA-T"
     ]
   }
   ```

### 4) Keep the rest in `slow`
- Everything not in medium stays in slow.
- Yes, there will be duplicates if you accidentally leave a point in slow and also add it to medium.  
  **Avoid duplicates**: pick one tier per point.

### 5) Save and validate
1. Click **Save Config**
2. Click **Generate YAML**
3. Confirm:
   - Medium tier shows your subset
   - Slow tier shows the bulk list
4. Optional: **YAML Diff** to verify

---

## Medium tuning tips
- If you notice load issues:
  - Move some points back to slow
  - Reduce `batch_size` slightly (e.g., 80)
- If you want a tiny fast tier:
  - Limit to points you’re actively debugging
  - Plan to remove them once the test is done

---

## Rollback plan (Medium)
1. Empty the medium tier points array (`"points": []`)
2. Put everything back into slow
3. Save, then generate YAML

