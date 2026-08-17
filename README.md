<div align="center">
  <img src="assets/spotify.svg" width="100" align="center">
  <h1>Spotify Readme</h1>
</div>

<p align="center">
  A dynamic, simple and real-time Spotify Play Now widget for your README files that syncs with the currently playing song. If you're not currently playing a song, one of your recent songs will be displayed! Feel free to ask for help or ask any PR/problem/suggestion 😄
</p>

## Previews

#### Default
```
/api
```
![setup-screenshot](assets/preview.png)


## Widgets

| Endpoint | Shows |
|---|---|
| `/api` | Currently playing (or most recent) track, with an animated EQ and a progress bar showing elapsed/total duration |
| `/api/top` | Your top 5 tracks over the last ~4 weeks (requires the `user-top-read` scope — see setup below) |
| `/api/recent` | Your last 5 played tracks |

Every widget accepts the same customization query params, e.g. `/api?theme=dark&bg=1a1a1a&bars=8`:

| Param | Values | Effect |
|---|---|---|
| `theme` | `light` (default) or `dark` | Text/muted/accent colors tuned for a light or dark README background |
| `bg` | A 3 or 6-digit hex color, with or without `#` (e.g. `bg=1a1a1a`) | Background color behind the widget; omit for a transparent background |
| `bars` | An integer 4–20 (`/api` only) | Number of animated equalizer bars |

## Project Structure

The codebase follows a simple clean-architecture split: `api/` is a thin serverless entrypoint (required by Vercel's routing convention), while all actual logic lives in the `app/` package.

```
spotify-readme/
├── api/
│   ├── index.py          # Vercel entrypoint — creates and exposes the Flask app
│   └── requirements.txt  # Python dependencies (kept alongside the entrypoint for Vercel's builder)
├── app/
│   ├── __init__.py       # Flask app factory + the /api, /api/top, /api/recent routes
│   ├── config.py         # Env loading, constants, and the base64 logo
│   ├── spotify_client.py # Spotify OAuth token exchange + authenticated requests (SpotifyError)
│   ├── theming.py         # Validates/resolves the theme, bg, and bars query params
│   ├── widgets/
│   │   ├── now_playing.py     # currently-playing → recently-played → last-known → fallback chain, with progress bar
│   │   ├── top_tracks.py      # Top-tracks widget (me/top/tracks)
│   │   ├── recently_played.py # Recently-played list widget
│   │   └── _track_list.py     # Shared rendering for the two list-style widgets
│   ├── templates/
│   │   ├── now_playing.html   # SVG/Jinja2 template for the now-playing widget
│   │   └── track_list.html    # Shared SVG/Jinja2 template for the top-tracks and recently-played widgets
│   └── assets/
│       └── spotify_logo.txt  # Base64-encoded Spotify logo inlined into the SVG
├── assets/                # README-only images (preview screenshot, logo source)
└── vercel.json             # Rewrites all paths to the serverless function
```

## Setup/Deployment

#### 1. Spotify's API

* Head over to the <a href="https://developer.spotify.com/dashboard/">Spotify developer portal</a>.
  * Create a Spotify application.
    * In the **App name** & **App description** fields, you may put whatever you want.
    * Agree with Spotify's TOS and click **Create**.
  * Take note of the **Client ID** & **Client Secret**.
  * Click **Edit Settings**.
    * Add `http://127.0.0.1:8888/callback` to **Redirect URIs**.

#### 2. Intermediary Steps

```
https://accounts.spotify.com/authorize?client_id={CLIENT_ID}&response_type=code&scope=user-read-currently-playing,user-read-recently-played,user-top-read&redirect_uri=http://127.0.0.1:8888/callback
```

The `user-top-read` scope is only needed for the `/api/top` widget. If you don't care about that widget you can drop it from the URL above, but note that a `refresh_token` obtained without it will make `/api/top` render an empty "Nothing to show right now" widget instead of erroring.

* Copy and paste the above link into your browser.
  * Replace `{CLIENT_ID}` with the **Client ID** you got from your Spotify application.
  * Vist the URL.
    * Log in if you're not already signed in.
    * Click **Agree**.
  * After you get redirected to a blank page, retrieve the URL from your browser's URL bar. It should be in the following format: `http://127.0.0.1:8888/callback?code={CODE}`.
  * Take note of the `{CODE}` portion of the URL.
* Generate the Base64 value locally; do not send your client secret to an online encoder:
  * On macOS/Linux, run `printf '%s' '{CLIENT_ID}:{CLIENT_SECRET}' | base64`.
  * Take note of the generated value and avoid committing it or sharing it publicly.
* If you're on Windows or don't have the `curl` command, head over to <a href="https://httpie.io/cli/run">httpie.io/cli/run</a>.
  * Press enter.
  * Clear the pre-filled command.
* If you're on Linux or Mac with the `curl` command, open up your preferred terminal.
* Run the following command (replace `{BASE_64}` and `{CODE}` with their respective values):

  ```
  curl -X POST -H "Content-Type: application/x-www-form-urlencoded" -H "Authorization: Basic {BASE_64}" -d "grant_type=authorization_code&redirect_uri=http://127.0.0.1:8888/callback&code={CODE}" https://accounts.spotify.com/api/token
  ```

* If you did everything correctly, you should get a response in the form of a JSON object.
  * Take note of the `refresh_token`'s value.

#### 3. Host on Vercel

* Fork this repository.
* Head over to <a href="https://vercel.com">Vercel</a> and create an account if you don't already have one.
  * Add a new project on Vercel.
    * Link your GitHub account if you haven't done so already.
    * Make sure Vercel has access to the forked respository.
    * Import the forked respository into your project.
      * Give it a meaningful project name.
      * Keep the default options for the other settings.
      * Add the following environment variables along with their appropriate values:
        * `CLIENT_ID`
        * `CLIENT_SECRET`
        * `REFRESH_TOKEN`
      * Click **Deploy**.
      * Click **Continue to Dashboard**.
        * Find the **Domains** field and take note of the URL.
          * Example: `{PROJECT_NAME}.vercel.app`.

#### 4. Add to your GitHub

* In any markdown file, add the following (replace `{PROJECT_NAME}` with the name you gave your Vercel project):

```html
<img src="https://{PROJECT_NAME}.vercel.app/api" alt="Current Spotify Song">
```

The widget is designed to always return a valid SVG. If Spotify is unavailable,
there is no current track, or the playback history is empty, it shows a neutral
fallback instead of exposing an error. Keep `CLIENT_ID`, `CLIENT_SECRET`, and
`REFRESH_TOKEN` only in Vercel environment variables; never commit them to the repository.

## Note

This wasn't a completely original idea. This was inspired by <a href="https://github.com/novatorem/novatorem">novatorem's project</a> that was supposed to be for me only. Since others have asked for the source code, I decided to make this a public repo. I also incorporated the latest two PR's from the orignal project into this one and made it easy to customize!

<sub>**This feature is a fork of [tthn0](https://github.com/tthn0)**</sub>

<!-- deployment marker -->
