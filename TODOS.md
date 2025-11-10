# TODOS - ADHD-Friendly Voice Reminders System

**Last Updated:** November 9, 2025, 7:20 PM
**Status:** Active Development - Bug Fixes & Polish

---

## 🐛 CRITICAL BUGS (Fix ASAP)

### 1. Sync Failing: "table reminders has no column named distance" 🔥
**Status:** Identified - Ready to Fix
**Priority:** CRITICAL
**Impact:** Sync completely broken when location-based reminders are involved

**Issue:**
Backend logs show sync errors:
```
ERROR: Failed to apply change b9bfe49f-9000-48a5-a89a-e960fd99cb6e:
Execute failed: table reminders has no column named distance
```

**Root Cause:**
1. In `/api/reminders/near-location` endpoint (`server/main.py:414`), the code adds a computed field:
   ```python
   reminder['distance'] = round(distance, 2)  # Add metadata for sorting
   ```
2. This reminder (with `distance` field) gets synced to the client
3. Client sends it back in sync request
4. Server's `apply_sync_change()` → `update_reminder()` tries to UPDATE with `distance` field
5. SQLite throws error because `distance` column doesn't exist in schema

**Fix Required:**
Add field filtering in `server/database.py:322` (update_reminder function):

```python
def update_reminder(reminder_id: str, update_data: Dict[str, Any]) -> bool:
    """
    Update reminder fields.

    Args:
        reminder_id: Reminder ID to update
        update_data: Dictionary of fields to update

    Returns:
        True if reminder was updated
    """
    if not update_data:
        return False

    # ✅ ADD THIS: Define allowed database columns
    ALLOWED_FIELDS = {
        'text', 'notes', 'due_date', 'due_time', 'time_required',
        'location_name', 'location_address', 'location_lat', 'location_lng', 'location_radius',
        'priority', 'category', 'status', 'completed_at', 'snoozed_until', 'snooze_count',
        'recurrence_id', 'is_recurring_instance', 'original_due_date',
        'source', 'created_at', 'updated_at', 'synced_at'
    }

    # ✅ ADD THIS: Filter out non-database fields (like 'distance')
    filtered_data = {k: v for k, v in update_data.items() if k in ALLOWED_FIELDS}

    if not filtered_data:
        return False

    # Build dynamic UPDATE using filtered data
    set_clause = ", ".join([f"{field} = ?" for field in filtered_data.keys()])
    values = list(filtered_data.values())
    values.append(reminder_id)

    query = f"UPDATE reminders SET {set_clause} WHERE id = ?"
    affected = db_execute(query, tuple(values))

    return affected > 0
```

**Testing:**
- [ ] Query `/api/reminders/near-location` → Returns reminders with `distance`
- [ ] Trigger sync → No error in logs
- [ ] Verify reminder syncs correctly without `distance` field in DB
- [ ] Check that `distance` is still returned in API responses (just not persisted)

---

### 2. MapBox "Style is not done loading" Error ⚠️
**Status:** In Progress
**Priority:** High
**Impact:** Blocks location picker from working smoothly

**Issue:**
When selecting a location (search or "Use My Location"), a browser alert appears:
```
localhost:3077
Style is not done loading
[OK]
```
After dismissing, the map works perfectly. This is a race condition bug.

**Root Cause:**
In `public/js/location-picker.js:308`, `updateRadiusCircle()` is called immediately after map creation (line 251), but the map style hasn't finished loading yet. When `MapBoxUtils.addRadiusCircle()` tries to add layers/sources, MapBox throws an error because the style is still initializing.

**Fix Required:**
```javascript
// In showMap() function (public/js/location-picker.js ~line 250)
if (!map) {
  map = MapBoxUtils.createMap('locationMap', {
    center: [lng, lat],
    zoom: 14
  });

  // ✅ ADD THIS: Wait for style to load before adding layers
  map.on('load', () => {
    // Add or update marker
    if (!marker) {
      marker = MapBoxUtils.addDraggableMarker(map, lat, lng, async (newCoords) => {
        // ... existing drag handler ...
      });
    }

    // Add radius circle AFTER style loads
    updateRadiusCircle(lat, lng, currentLocation.radius);
  });

  // Add click handler
  map.on('click', async (e) => {
    // ... existing click handler ...
  });
} else {
  // Existing: fly to location and update
  map.flyTo({ center: [lng, lat], zoom: 14 });

  // Update marker and circle
  if (marker) {
    marker.setLngLat([lng, lat]);
  }
  updateRadiusCircle(lat, lng, currentLocation.radius);
}
```

**Testing:**
- [ ] Search for an address → No error dialog
- [ ] Click "Use My Location" → No error dialog
- [ ] Click on map → No error dialog
- [ ] Drag marker → No error dialog
- [ ] Adjust radius slider → No error dialog

---

### 3. Voice Transcription "Speak Up and Try Again" Error 🎤
**Status:** Investigating
**Priority:** High
**Impact:** Blocks voice input feature entirely

**Issue:**
Recording audio always returns:
```
No speech detected in audio. Please speak louder and try again.
```
Even when speaking clearly into microphone.

**Known Facts:**
- ✅ Whisper.cpp binary exists: `/whisper.cpp/build/bin/whisper-cli`
- ✅ Whisper model exists: `/whisper.cpp/models/ggml-base.en.bin` (148MB)
- ✅ Browser MediaRecorder API works (recording starts/stops)
- ✅ Audio file is created and uploaded to backend
- ❌ Whisper returns "[BLANK_AUDIO]" or no transcription

**Possible Causes:**
1. **Audio codec incompatibility** - Browser records WebM/Opus, Whisper may need WAV
2. **Sample rate mismatch** - Recording at 16kHz but Whisper expects 16kHz (should work)
3. **Audio too short** - Whisper may reject very short recordings
4. **Volume too low** - Recording level not detected
5. **FFmpeg conversion issue** - Whisper.cpp's built-in conversion failing

**Investigation Steps:**
- [ ] Test with a longer recording (10+ seconds)
- [ ] Check backend logs for Whisper.cpp stderr output
- [ ] Save recorded audio file to disk and manually test with Whisper CLI:
  ```bash
  /path/to/whisper-cli -m /path/to/ggml-base.en.bin -f test-recording.webm
  ```
- [ ] Add FFmpeg pre-conversion in backend (WebM → WAV 16kHz mono):
  ```bash
  ffmpeg -i input.webm -ar 16000 -ac 1 output.wav
  ```
- [ ] Add audio visualization to frontend to confirm recording is capturing sound

**Files to Check:**
- `server/voice/whisper.py:39-148` - Transcription logic
- `server/main.py:440-552` - Voice upload endpoint
- `public/js/voice-recorder.js` - Recording settings

---

### 4. Location Search Error Dialog (Non-Blocking) ⚠️
**Status:** Identified
**Priority:** Medium
**Impact:** Confusing UX, but feature works after dismissing error

**Issue:**
When searching for an address in location picker, an error alert appears:
```
Could not find that location. Please try a different address.
```
But after dismissing, search results appear and work perfectly.

**Root Cause:**
Likely a try/catch block is catching an error from MapBox API and showing alert, even though the request actually succeeded. Need to investigate `location-picker.js:103-133` (handleAddressSearch).

**Fix Required:**
- [ ] Review error handling in `handleAddressSearch()`
- [ ] Check if MapBox API is returning non-standard error format
- [ ] Only show alert if geocoding truly fails (empty results)

---

## 💾 DATA ISSUES

### 5. Missing Test Reminders in Cloudflare D1 ❓
**Status:** Resolved (No Data Loss)
**Priority:** Low

**Report:**
Expected 750 test reminders in Cloudflare D1, but only 7 seed reminders exist.

**Investigation Results:**
- ✅ Checked remote D1: `SELECT COUNT(*) FROM reminders` → **7 reminders**
- ✅ Checked git history: No commits with "750" or bulk test data
- ✅ Current D1 data:
  - 7 seed reminders created Nov 3, 2025
  - IDs: `seed-00000000-0000-0000-0000-000000000001` through `000007`
  - Categories: Personal, Work
  - Status: All pending

**Conclusion:**
The 750 reminders were likely in a **local development database** that was cleared during project reorganization (commits `e3ec1fb` and `3d1f03d` on Nov 8-9). They were never synced to Cloudflare D1, so no data was lost from production.

**Action Items:**
- [ ] ✅ DONE: Local database now initialized with fresh schema
- [ ] Optional: Create script to seed realistic test data
- [ ] Optional: Sync existing 7 cloud reminders to local on first run

---

## 🎨 UI/UX POLISH

### 6. Create Proper Favicon
**Status:** Done
**Priority:** Low

- [x] Created empty `public/favicon.ico` to stop 404 errors
- [ ] Optional: Design actual icon for the app

---

## 📋 COMPLETED ITEMS

- [x] **Create `run_dev.py` startup script** - One command to run both backend + frontend
- [x] **Initialize empty local database** - Fixed 0-byte reminders.db
- [x] **Fix missing secrets.json** - Already configured
- [x] **Verify Whisper.cpp installation** - Binary and model confirmed
- [x] **Check Cloudflare Workers deployment** - Active (last deploy: Nov 3, 2025)
- [x] **Verify sync architecture** - Local ↔ Cloud bidirectional sync working

---

## 🚀 QUICK START REFERENCE

```bash
# Stop any running servers (Ctrl+C)

# Start everything (backend + frontend + database init)
python run_dev.py

# Force reinitialize database
python run_dev.py --init

# Open in browser
open http://localhost:3077
```

**URLs:**
- Frontend: http://localhost:3077
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/api/health

---

## 📁 FILES TO EDIT

**For Sync Fix (PRIORITY #1):**
- `server/database.py` (lines 322-344, update_reminder function)

**For MapBox Fix:**
- `public/js/location-picker.js` (lines 245-310)

**For Voice Fix:**
- `server/voice/whisper.py` (add FFmpeg conversion)
- `public/js/voice-recorder.js` (add audio visualization)

**For Location Search Fix:**
- `public/js/location-picker.js` (lines 103-133)

---

## 🧪 TESTING CHECKLIST

After fixes are applied:

**Voice Recording:**
- [ ] Record 5-second audio → Transcribes successfully
- [ ] Record 15-second audio → Transcribes successfully
- [ ] Record with background noise → Handles gracefully
- [ ] Record silence → Shows appropriate error

**Location Picker:**
- [ ] Search address → No error, shows results
- [ ] Click "Use My Location" → No error, shows current location
- [ ] Click on map → No error, moves marker
- [ ] Drag marker → No error, updates location
- [ ] Adjust radius → Updates circle smoothly
- [ ] Clear location → Resets form

**Sync:**
- [ ] Create reminder locally → Syncs to cloud (check D1)
- [ ] Create reminder in cloud → Syncs to local
- [ ] Edit reminder → Conflict resolution works
- [ ] Delete reminder → Deletes on both sides

---

**Next Session Focus:** Fix MapBox race condition → Test voice transcription → Polish error messages
