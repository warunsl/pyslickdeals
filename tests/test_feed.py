from slickdeals.cli import _matches, main
from slickdeals.feed import feed_url, parse_feed

SAMPLE = b"""<?xml version="1.0"?>
<rss version="2.0" xmlns:dc="http://purl.org/dc/elements/1.1/">
  <channel>
    <title>Slickdeals Frontpage RSS Feed</title>
    <item>
      <title><![CDATA[Bosch 300 Series Dishwasher $499 + Free Pickup &amp; More]]></title>
      <link>https://slickdeals.net/f/20401413-bosch-dishwasher?utm_source=rss&amp;utm_content=fp&amp;utm_medium=RSS2</link>
      <description>Lowe's has the Bosch &amp;quot;300&amp;quot; for $499.</description>
      <pubDate>Thu, 26 Nov 2026 23:32:13 +0000</pubDate>
      <guid>thread-20401413</guid>
    </item>
    <item>
      <title><![CDATA[Gerhart Coffee 45% Off]]></title>
      <link>https://slickdeals.net/f/20400783-gerhart-coffee?utm_source=rss</link>
      <description>Small business coffee sale.</description>
      <pubDate>not a date</pubDate>
      <guid>thread-20400783</guid>
    </item>
  </channel>
</rss>"""


def test_parse_feed():
    deals = parse_feed(SAMPLE)
    assert [d.id for d in deals] == ["20401413", "20400783"]
    first = deals[0]
    assert first.title == "Bosch 300 Series Dishwasher $499 + Free Pickup & More"
    assert first.link == "https://slickdeals.net/f/20401413-bosch-dishwasher"
    assert first.description == 'Lowe\'s has the Bosch "300" for $499.'
    assert first.published.year == 2026
    assert deals[1].published is None
    assert first.to_dict()["published"].startswith("2026-11-26")


def test_feed_url():
    assert "mode=frontpage" in feed_url()
    assert "mode=popdeals" in feed_url(popular=True)
    url = feed_url("air pods")
    assert "q=air+pods" in url and "mode=" not in url


def test_matches():
    deal = parse_feed(SAMPLE)[0]
    assert _matches(deal, ["BOSCH"])
    assert _matches(deal, ["nope", "lowe"])
    assert not _matches(deal, ["airpods"])


def test_cli_json(monkeypatch, capsys):
    import json

    monkeypatch.setattr("slickdeals.cli.fetch_deals", lambda q, popular: parse_feed(SAMPLE))
    assert main(["--json", "-n", "1"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert len(out) == 1 and out[0]["id"] == "20401413"
    assert "hot" not in out[0]
