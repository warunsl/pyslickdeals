# pyslickdeals

Browse [Slickdeals](https://slickdeals.net) from the command line.

Reads Slickdeals' public RSS feeds, so it doesn't break every time the site's
HTML changes. No third-party dependencies, only the Python standard library.

## Install

```sh
uv tool install .          # puts `slickdeals` on your PATH
# or, without installing:
uv run slickdeals
```

## Usage

```sh
slickdeals                      # frontpage deals
slickdeals -n 10 -v             # top 10, with descriptions
slickdeals -p                   # 🔥 popular deals
slickdeals -s "airpods pro"     # search all deals
slickdeals -m tv -m monitor     # frontpage deals mentioning tv OR monitor
slickdeals --json | jq '.[].title'

# Poll every 5 minutes for new matching deals, with macOS notifications
slickdeals -w -i 5 -s "lg oled" --notify
```

## Development

```sh
uv run pytest
```
