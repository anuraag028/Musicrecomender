# Viva Examination Guide: Social-Aware Hybrid Music Recommender System (TWSMA)

This guide provides a structured 5-minute demonstration script, actual runtime mathematical walkthroughs, anticipated examiner questions, and transparent architectural disclosures for your project defense.

---

## 1. Five-Minute Demonstration Sequence

### Step 1: System Health & Provider Telemetry (0:00 - 1:00)
1. Open the web application at `http://127.0.0.1:5173`.
2. Point out the **Provider Health Indicators** in the top navbar:
   - MusicBrainz WS/2: `HEALTHY` (Rate limited to 1 req/sec).
   - Last.fm API: `HEALTHY` (or `KEY_REQUIRED` honest disclosure).
   - YouTube Playback: `HEALTHY` (Verified Video or Search Embed active).
   - TWSMA Text Engine: `HEALTHY` (Pitchfork RSS feed ingested).
3. Emphasize the **Strict Data Integrity Policy**: Zero fake song titles or listener counts are manufactured.

### Step 2: Demo Profiles & Cold-Start Distinction (1:00 - 2:00)
1. In the **Demo Profiles** selector, show the 3 labelled profiles:
   - **Alex Vance** (`demo-user-1`): Indie Rock, Post-Punk, Shoegaze.
   - **Beatrix Chen** (`demo-user-2`): Pop, Dance, Electropop.
   - **Charlie Miller** (`demo-user-3`): Electronic, Synthwave, Ambient.
2. Note the banner: **`SYNTHETIC / DEMO PROFILE`**. User interaction data is kept completely isolated from the real external music catalogue.
3. Switch between **Alex Vance** and **Beatrix Chen**, showing how their genre preferences immediately alter the Content-Based TF-IDF vectors.

### Step 3: Hybrid Recommendation & Numeric Explainability (2:00 - 3:30)
1. On the **For You** tab, click **"Generate My Playlist"**.
2. Show the ranked tracks with rank badges (`#1`, `#2`, `#3`), Match % scores, and playback provider status.
3. Click on the **Explainability & Trace** tab:
   - Highlight the **Candidate Funnel**:
     $$\text{Retrieved} \rightarrow \text{Deduplicated} \rightarrow \text{Excluded (Played/Skipped)} \rightarrow \text{Playback Eligible} \rightarrow \text{Scored} \rightarrow \text{Selected}$$
   - Highlight the **Mathematical Model**:
     $$\text{Hybrid Score} = \sum_{c \in \text{Available}} w_{\text{eff}}(c) \times S_c$$
   - Walk through the **Effective Weight Renormalization**: If a signal is missing (e.g. no news mentions for an indie track), the remaining active weights are scaled proportionally so their sum is strictly $1.00$.
   - Show the full JSON trace and click **"Copy Full Trace JSON"**.

### Step 4: Real Playback & Interactive Feedback Loop (3:30 - 4:15)
1. Click the **Play** button on any recommended track card.
2. The persistent bottom player activates:
   - Audio streams legitimately via the YouTube IFrame player.
   - Show the **"Show Video"** toggle button to reveal the embedded player window.
3. Click the **Thumbs Up** or **Skip** button:
   - Explain how `POST /api/interactions` records this action ($+1.0$ for like, $-0.5$ for skip).
   - Switch to the **Listening History** tab to prove the action was logged with the label **`LIVE SESSION`**, distinct from **`SYNTHETIC SEED`**.

### Step 5: TWSMA Text Analytics Pipeline (4:15 - 5:00)
1. Navigate to the **TWSMA Analytics** tab.
2. Demonstrate how real music news headlines from Pitchfork are ingested, stripped of HTML, filtered for stopwords, and processed with VADER sentiment analysis.
3. Show the **Extracted Domain Keywords** cloud and the compound valence score table.

---

## 2. Sample Formula Walkthrough (Actual Runtime Values)

Consider track *Lykanthropie (Monozelle remix)* evaluated for *Alex Vance*:

### Configured Default Weights:
$$w_{\text{content}} = 0.40, \quad w_{\text{collab}} = 0.30, \quad w_{\text{trend}} = 0.20, \quad w_{\text{text}} = 0.10$$

### Runtime Signal Availability:
1. **Content**: Available ($S_{\text{content}} = 0.9470$ via TF-IDF cosine similarity).
2. **Collaborative**: Unavailable (No peer interactions on this recording yet, $S_{\text{collab}} = \text{null}$).
3. **Trend**: Available ($S_{\text{trend}} = 0.9800$, Chart Rank #2 from MusicBrainz).
4. **TWSMA Text**: Unavailable (No recent mentions in current news articles, $S_{\text{text}} = \text{null}$).

### Dynamic Renormalization:
$$\text{Sum of available configured weights} = 0.40 + 0.20 = 0.60$$

$$\text{Effective Weight (Content)} = \frac{0.40}{0.60} = 0.6667$$

$$\text{Effective Weight (Trend)} = \frac{0.20}{0.60} = 0.3333$$

$$\text{Sum of Effective Weights} = 0.6667 + 0.3333 = 1.0000$$

### Final Hybrid Score Calculation:
$$\text{Final Score} = (0.6667 \times 0.9470) + (0.3333 \times 0.9800) = 0.6314 + 0.3266 = 0.9580 \quad (95.8\% \text{ Match})$$

*Result is strictly bounded between $0.0$ and $1.0$, completely deterministic, and verified by unit tests.*

---

## 3. Likely Examiner Questions & Recommended Answers

### Q1: Why didn't you train a deep learning neural network (e.g. Two-Tower / Transformer recommender)?
> **Answer**: In industrial and academic recommender systems, transparency and cold-start explainability are critical prerequisites before deploying black-box models. Furthermore, deep collaborative filtering models require massive user clickstream matrices ($>10^6$ rows) to avoid severe overfitting. Our hybrid architecture combines vector-space Content filtering, user-item Collaborative filtering, and real-time TWSMA sentiment with dynamic renormalization, providing deterministic explainability and mathematically auditable recommendations.

### Q2: How do you prevent data leakage in collaborative filtering?
> **Answer**: Target user future actions are never fed into the candidate generation pipeline. In `RecommendationEngine._compute_collaborative_scores()`, the target user's interaction row is strictly excluded from peer rating aggregations. Ratings are predicted solely from the cosine similarity of peer users over historical interactions.

### Q3: How do you handle external API rate limits (MusicBrainz and Last.fm)?
> **Answer**: MusicBrainz enforces a strict 1 request/second rate limit. We implemented a thread-safe token bucket limiter (`MusicBrainzRateLimiter`) with exponential backoff retries. Successful API responses are cached in SQLite (`api_cache` table) with provenance timestamps and TTL expiration to prevent unnecessary network overhead.

### Q4: How is TWSMA text sentiment different from chart play counts?
> **Answer**: Chart metrics (e.g., Last.fm playcounts or Billboard ranks) reflect passive consumption. TWSMA measures active cultural discourse and journalistic sentiment. A song may have high streams but negative press, or vice versa. By extracting text from Pitchfork music news and computing VADER valence, we derive an independent sentiment signal.

---

## 4. Honest System Limitations

1. **YouTube Embed Autoplay Policies**: Modern web browsers restrict autoplaying media unless the user has actively clicked the page. We support user-initiated play and clear audio/video toggle controls.
2. **Music News Coverage Asymmetry**: Mainstream artists appear frequently in RSS news feeds, while niche indie tracks may have zero news mentions. The system addresses this honestly: the text signal is marked `available: false` with zero fabricated sentiment, and remaining weights are renormalized.
3. **Synthetic Demo Histories**: Because user clickstreams require long-term deployment, demo user interaction histories are simulated for evaluation, clearly labelled **`SYNTHETIC SEED`**, and kept separate from live session interactions.
