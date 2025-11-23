# Svelte Migration Guide

> **Status**: Future consideration - not currently planned
> **Created**: 2025-11-23
> **Purpose**: Reference for converting vanilla JS frontend to SvelteKit

---

## Current Architecture

### Frontend Stack
- **10 JS modules** (~4,000 lines) in `/public/js/`
- **5 HTML pages**: index, upcoming, future, edit, settings
- **5 CSS files** in `/public/css/`
- **No build step** - files served directly
- **MapBox GL JS** for location features

### Key Modules to Migrate
| Module | Lines | Svelte Equivalent |
|--------|-------|-------------------|
| `app.js` | 858 | Page components + stores |
| `api.js` | ~200 | `$lib/api.ts` service |
| `sync.js` | ~300 | Store + background task |
| `storage.js` | ~150 | Svelte store with localStorage |
| `voice-recorder.js` | ~400 | `VoiceRecorder.svelte` |
| `location-picker.js` | ~500 | `LocationPicker.svelte` |
| `recurrence.js` | ~300 | `RecurrenceEditor.svelte` |

---

## Migration Approach

### 1. Setup SvelteKit
```bash
cd ProjectReminder
npx sv create frontend --template minimal --types ts
cd frontend
npm install
```

Keep `/public/` intact during migration for A/B comparison.

### 2. Project Structure
```
frontend/
├── src/
│   ├── lib/
│   │   ├── api.ts              # API client
│   │   ├── stores/
│   │   │   ├── reminders.ts    # Main data store
│   │   │   ├── config.ts       # Settings/localStorage
│   │   │   └── sync.ts         # Sync state
│   │   └── components/
│   │       ├── ReminderCard.svelte
│   │       ├── ReminderList.svelte
│   │       ├── VoiceRecorder.svelte
│   │       ├── LocationPicker.svelte
│   │       ├── RecurrenceEditor.svelte
│   │       ├── DateTimePicker.svelte
│   │       └── PrioritySelector.svelte
│   ├── routes/
│   │   ├── +page.svelte        # Today view (index)
│   │   ├── +layout.svelte      # Shared nav/layout
│   │   ├── upcoming/+page.svelte
│   │   ├── future/+page.svelte
│   │   ├── edit/[id]/+page.svelte
│   │   └── settings/+page.svelte
│   └── app.html
├── static/
│   └── (move static assets here)
├── svelte.config.js
└── vite.config.ts
```

### 3. State Management

**Reminders Store** (`src/lib/stores/reminders.ts`):
```typescript
import { writable, derived } from 'svelte/store';
import type { Reminder } from '$lib/types';

export const reminders = writable<Reminder[]>([]);

export const todayReminders = derived(reminders, $r =>
  $r.filter(r => isToday(r.due_date) || isOverdue(r.due_date))
);

export const upcomingReminders = derived(reminders, $r =>
  $r.filter(r => isUpcoming(r.due_date))
);
```

**Config Store** (localStorage persistence):
```typescript
import { writable } from 'svelte/store';
import { browser } from '$app/environment';

const stored = browser ? localStorage.getItem('config') : null;
export const config = writable(stored ? JSON.parse(stored) : defaults);

config.subscribe(value => {
  if (browser) localStorage.setItem('config', JSON.stringify(value));
});
```

### 4. API Client

Port `/public/js/api.js` to `$lib/api.ts`:
- Keep retry logic and local/cloud fallback
- Use fetch (SvelteKit handles it)
- Export typed functions

```typescript
export async function getReminders(): Promise<Reminder[]> {
  const response = await fetchWithRetry('/api/reminders');
  return response.json();
}
```

### 5. Component Migration Priority

**Phase 1 - Core Display** (get app running):
1. `+layout.svelte` - navigation
2. `ReminderCard.svelte` - single reminder display
3. `ReminderList.svelte` - list with sections
4. Today page (`+page.svelte`)

**Phase 2 - CRUD**:
5. Edit page with form
6. `PrioritySelector.svelte`
7. `DateTimePicker.svelte`

**Phase 3 - Advanced Features**:
8. `VoiceRecorder.svelte` - audio recording
9. `LocationPicker.svelte` - MapBox integration
10. `RecurrenceEditor.svelte`
11. Sync background task

---

## Key Challenges

### MapBox Integration
MapBox GL JS expects a DOM container. Use `onMount`:
```svelte
<script>
  import { onMount } from 'svelte';
  import mapboxgl from 'mapbox-gl';

  let mapContainer;
  let map;

  onMount(() => {
    map = new mapboxgl.Map({
      container: mapContainer,
      // ... config
    });
    return () => map.remove();
  });
</script>

<div bind:this={mapContainer} class="map"></div>
```

### Background Sync
Use `onMount` in `+layout.svelte` for app-wide sync:
```svelte
onMount(() => {
  const interval = setInterval(syncReminders, 5 * 60 * 1000);
  return () => clearInterval(interval);
});
```

### Voice Recording
MediaRecorder API works the same - just wrap in component with proper lifecycle cleanup.

### CSS Migration
Options:
1. **Scoped styles** - Move CSS into each component's `<style>` block
2. **Global + scoped** - Keep `main.css` global, scope component-specific styles
3. **Tailwind** - If you want to go that route

Recommendation: Start with option 2 (global base + scoped components).

---

## Build & Deployment

### Development
```bash
npm run dev
```

### Production Build
```bash
npm run build
```

Output goes to `build/` - static files ready for any host.

### SvelteKit Adapter
Use `@sveltejs/adapter-static` for static site generation:
```javascript
// svelte.config.js
import adapter from '@sveltejs/adapter-static';

export default {
  kit: {
    adapter: adapter({
      pages: 'build',
      assets: 'build',
      fallback: 'index.html' // SPA mode
    })
  }
};
```

---

## Testing Migration

Replace Jest with Vitest + Svelte Testing Library:

```bash
npm install -D vitest @testing-library/svelte jsdom
```

```typescript
// Example test
import { render, screen } from '@testing-library/svelte';
import ReminderCard from '$lib/components/ReminderCard.svelte';

test('displays reminder text', () => {
  render(ReminderCard, { props: { reminder: mockReminder } });
  expect(screen.getByText('Buy groceries')).toBeInTheDocument();
});
```

---

## Migration Checklist

- [ ] Initialize SvelteKit project in `/frontend`
- [ ] Set up TypeScript types for Reminder, Recurrence, etc.
- [ ] Port API client with retry/fallback logic
- [ ] Create stores (reminders, config, sync state)
- [ ] Build core components (Card, List, Layout)
- [ ] Implement all 5 page routes
- [ ] Port VoiceRecorder with MediaRecorder API
- [ ] Port LocationPicker with MapBox
- [ ] Port RecurrenceEditor
- [ ] Set up background sync in layout
- [ ] Migrate CSS (global base + scoped)
- [ ] Configure adapter-static for deployment
- [ ] Port tests to Vitest
- [ ] Update deployment pipeline
- [ ] Remove old `/public` directory

---

## Estimated Effort

- **Phase 1** (Core display): 2-3 days
- **Phase 2** (CRUD): 2-3 days
- **Phase 3** (Voice, Location, Sync): 3-5 days
- **Testing & Polish**: 2-3 days

**Total: 2-3 weeks** for a complete, tested migration.

---

## When to Pull This Trigger

Consider migration when:
- DOM manipulation in `app.js` becomes hard to follow
- Adding new views requires too much boilerplate
- State synchronization bugs increase
- You want TypeScript throughout the frontend

Don't migrate just because frameworks are trendy. The vanilla JS works.
