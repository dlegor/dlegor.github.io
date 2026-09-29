# dlegor.github.io

Personal site of Daniel Legorreta, served by GitHub Pages at <https://dlegor.github.io>.

Plain static HTML based on the [Strata](https://html5up.net/strata) template by HTML5 UP (CC BY 3.0, see `LICENSE.txt`).

## Blog sync from Medium

The **Blog** section of `index.html` lists the latest posts from
[Medium](https://medium.com/@d.legorreta.anguiano). Publish on Medium as usual, and they
show up here automatically:

- `.github/workflows/medium-sync.yml` runs every 6 hours (or on demand from the
  **Actions** tab → *Sync Medium posts* → *Run workflow*).
- It runs `scripts/sync_medium.py`, which reads the Medium RSS feed and rewrites the HTML
  between `<!-- MEDIUM:START -->` and `<!-- MEDIUM:END -->`, then commits if anything changed.
- If Medium is unreachable, the page is left as is.

Run it locally with `python3 scripts/sync_medium.py` (stdlib only), or test against a
saved feed with `--feed path/to/feed.xml`.

## Local preview

```sh
python3 -m http.server 8000
```

## Privacy checklist before adding files

- Strip image metadata (EXIF/XMP/GPS) before committing photos.
- Don't commit documents containing a phone number, email or address, because git history is public.
- Commit with your GitHub `noreply` email.
