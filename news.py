import feedparser
from datetime import datetime
import pytz

def get_high_impact_news():
    # Forex Factory RSS Feed
    url = "https://nfs.faireconomy.media/ff_calendar_thisweek.xml"
    try:
        feed = feedparser.parse(url)
        high_impact = []
        
        for entry in feed.entries:
            # We only want High Impact (Red Folder) news
            if "High" in entry.title:
                high_impact.append(f"🔴 {entry.title}")
                
        if not high_impact:
            return "No High-Impact news scheduled."
        
        # Return top 5 news events for the week/day
        return "\n".join(high_impact[:5])
    except Exception as e:
        return f"Error fetching news: {e}"

def get_session_status():
    # Uses Nigerian Time (WAT)
    tz = pytz.timezone('Africa/Lagos')
    now = datetime.now(tz)
    hour = now.hour

    if 1 <= hour < 8:
        return "🗼 **Tokyo Session (Asian)** - Usually slow, beware of fakeouts."
    elif 8 <= hour < 13:
        return "💂 **London Session** - High volume, great for breakouts."
    elif 13 <= hour < 21:
        return "🗽 **New York Session** - Most volatile, overlaps with London."
    else:
        return "💤 **Sydney Session** - Market is mostly resting."
