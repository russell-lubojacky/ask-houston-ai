<script lang="ts">
  import { onMount } from 'svelte';
  import { browser } from '$app/environment';

  let query = '';
  let results: any[] = [];
  let loading = false;
  let error = '';
  let map: any = null;
  let mapContainer: HTMLElement;
  let markers: any[] = [];
  let L: any = null; // Will be loaded dynamically

  onMount(async () => {
    if (browser) {
      // Dynamically import Leaflet only in the browser
      L = (await import('leaflet')).default;
    }
  });

  async function ask() {
    // Frontend validation
    if (!query || query.trim().length === 0) {
      error = 'Please enter a question';
      return;
    }

    if (query.length > 1000) {
      error = 'Question is too long (max 1000 characters)';
      return;
    }

    // Basic check for suspicious patterns
    const suspiciousPatterns = [
      /DROP\s+TABLE/i,
      /DELETE\s+FROM/i,
      /INSERT\s+INTO/i,
      /UPDATE\s+.*SET/i,
      /TRUNCATE/i,
      /ALTER\s+TABLE/i
    ];

    for (const pattern of suspiciousPatterns) {
      if (pattern.test(query)) {
        error = 'Your question contains invalid keywords. Please ask about Houston 311 incidents.';
        return;
      }
    }

    loading = true;
    error = '';
    results = [];

    try {
      const res = await fetch(`/ask?q=${encodeURIComponent(query)}`);
      const data = await res.json();

      // Check for backend errors
      if (data.error) {
        error = data.error;
        results = [];
      } else {
        results = data.results || [];

        // Initialize map if needed and update with markers
        console.log('Results:', results);
        if (results.length > 0) {
          setTimeout(() => initializeAndUpdateMap(), 100);
        }
      }
    } catch (err) {
      error = 'Network error. Please try again.';
    }
    loading = false;
  }

  function initializeAndUpdateMap() {
    // Check if Leaflet is loaded
    if (!L) {
      console.error('Leaflet not loaded yet');
      return;
    }

    // Initialize map on first use
    if (!map && mapContainer) {
      console.log('Creating map with Leaflet');
      map = L.map(mapContainer).setView([29.7604, -95.3698], 11);
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19
      }).addTo(map);
    }

    if (!map) {
      console.error('Map failed to initialize');
      return;
    }

    // Clear existing markers
    markers.forEach(marker => marker.remove());
    markers = [];

    // Add new markers for results with lat/lng
    const validPoints: L.LatLngExpression[] = [];

    results.forEach((result) => {
      const lat = parseFloat(result.latitude);
      const lng = parseFloat(result.longitude);

      console.log('Processing result:', result, 'Lat:', lat, 'Lng:', lng);

      if (!isNaN(lat) && !isNaN(lng) && lat !== 0 && lng !== 0) {
        const marker = L.marker([lat, lng]).addTo(map!);

        // Create popup with incident details
        const popupContent = `
          <strong>${result.incident_case_type || 'Incident'}</strong><br/>
          ${result.incident_address || ''}<br/>
          Status: ${result.status || 'N/A'}<br/>
          Date: ${result.created_date_utc ? new Date(result.created_date_utc).toLocaleDateString() : 'N/A'}
        `;
        marker.bindPopup(popupContent);

        markers.push(marker);
        validPoints.push([lat, lng]);
      }
    });

    // Fit map to show all markers
    if (validPoints.length > 0) {
      const bounds = L.latLngBounds(validPoints);
      map.fitBounds(bounds, { padding: [50, 50] });
    }
  }
</script>

<svelte:head>
  <title>Ask Houston AI</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
    integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY="
    crossorigin=""/>
</svelte:head>

<style>
  :global(body) {
    font-family: 'Inter', sans-serif;
    background: #fdfdfd;
    margin: 0;
    padding: 0;
    color: #222;
  }

  .container {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding-top: 15vh;
  }

  h1 {
    font-size: 2.5rem;
    color: #002D62; /* Texans dark blue */
    margin-bottom: 2rem;
  }

  input[type="text"] {
    width: 400px;
    font-size: 1.2rem;
    padding: 0.5rem 1rem;
    border: 2px solid #FF6A13; /* Astros orange */
    border-radius: 6px;
    outline: none;
  }

  .input-block {
    display: flex;
    flex-direction: column;
    align-items: center;
  }

  textarea {
    width: 600px;
    font-size: 1.2rem;
    padding: 0.75rem 1rem;
    border: 2px solid #FF6A13;
    border-radius: 6px;
    resize: vertical;
    outline: none;
  }

  .button-row {
    margin-top: 1rem;
  }

  .char-counter {
    font-size: 0.85rem;
    color: #666;
    margin-top: 0.25rem;
    align-self: flex-end;
  }

  .char-counter.warning {
    color: #FF6A13;
  }

  button {
    font-size: 1.2rem;
    padding: 0.5rem 1.5rem;
    background-color: #002D62;
    color: white;
    border: none;
    border-radius: 6px;
    cursor: pointer;
  }

  button:hover {
    background-color: #163E6C;
  }

  .results {
    margin-top: 3rem;
    width: 90%;
    overflow-x: auto;
  }

  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.9rem;
  }

  th, td {
    border: 1px solid #ddd;
    padding: 6px 10px;
    text-align: left;
    white-space: nowrap;
  }

  th {
    background-color: #f3f3f3;
    position: sticky;
    top: 0;
  }

  .error {
    color: red;
    margin-top: 1rem;
  }

  .map-container {
    width: 90%;
    height: 500px;
    margin-top: 2rem;
    border: 2px solid #002D62;
    border-radius: 8px;
    overflow: hidden;
  }

  :global(.leaflet-container) {
    height: 100%;
    width: 100%;
  }
</style>

<div class="container">
  <h1>Ask Houston AI</h1>
  <div class="input-block">
    <textarea
        bind:value={query}
        rows="3"
        placeholder="Ask about Houston 311 incidents (potholes, graffiti, trash, etc.)..."
        on:keydown={(e) => e.ctrlKey && e.key === 'Enter' && ask()}
    ></textarea>
    <div class="char-counter" class:warning={query.length > 900}>
      {query.length} / 1000 characters
    </div>
    <div class="button-row">
        <button on:click={ask}>Ask</button>
    </div>
  </div>

  {#if loading}
    <p>Loading brotha...</p>
  {/if}

  {#if error}
    <p class="error">{error}</p>
  {/if}

  {#if results.length > 0}
    <div class="map-container" bind:this={mapContainer}></div>
  {/if}

  {#if results.length > 0}
    <div class="results">
      <table>
        <thead>
          <tr>
            {#each Object.keys(results[0]) as key}
              <th>{key}</th>
            {/each}
          </tr>
        </thead>
        <tbody>
          {#each results as row}
            <tr>
              {#each Object.values(row) as val}
                <td>{val}</td>
              {/each}
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
</div>
