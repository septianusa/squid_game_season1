import requests
from bs4 import BeautifulSoup
import pandas as pd
from google.colab import files

# ======================
# Scraper function
# ======================
def generate_players(n: int = 200) -> pd.DataFrame:
    df = pd.DataFrame({"Player Number": range(1, n + 1)})

    # Format with leading zeros to 3 digits (e.g., 001, 045, 200)
    df["Player Number"] = df["Player Number"].astype(str).str.zfill(3)

    # Add aesthetic label
    df["Player"] = "Player " + df["Player Number"]

    return df

# Generate Player Number
players_df = generate_players(200)

def scrape_player(url):
    """Scrape a single Squid Game player page and return dict with cleaned schema"""
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "lxml")
    except Exception as e:
        print(f"❌ Error fetching {url}: {e}")
        return None

    def get_value(source):
        tag = soup.select_one(f'div[data-source="{source}"] .pi-data-value')
        return tag.get_text(strip=True) if tag else "-"

    def get_text(selector):
        tag = soup.select_one(selector)
        return tag.get_text(strip=True) if tag else "-"

    def get_img():
        tag = soup.select_one("figure.pi-image img")
        return tag["src"] if tag else "-"

    # Core fields
    name           = get_value("name")
    aliases        = get_value("aliases")
    relationship   = get_value("relationships")
    affiliation    = get_value("affiliation")
    status         = get_value("status")
    occupation     = get_value("occupation")
    died           = get_value("died")
    games          = get_value("games")
    cause_of_death = get_value("cause")
    gender         = get_value("gender")
    eyes           = get_value("eyes")
    hair           = get_value("hair")

    # Extract player number from URL
    player_number = url.split("Player_")[1].split("_")[0]

    # Image
    image_url = get_img()

    return {
        "character_type": "Background",  # default for wiki-only players
        "name": name,
        "player_number": f"Player {player_number}",
        "other_alias": aliases,
        "relationship": relationship,
        "affiliation": affiliation,
        "status_at_end_game": status,
        "Occupation": occupation,
        "Died": died,
        "Games": games,
        "Cause of death": cause_of_death,
        "Gender": gender,
        "Eye Color": eyes,
        "Hair Color": hair,
        "Url": url,
        "Image URL": image_url
    }

# ======================
# Run on list of URLs
# ======================
def scrape_all_players(df_with_urls):
    records = []
    for _, row in df_with_urls.iterrows():
        url = row["URL"]
        print(f"🔎 Scraping {url} ...")
        data = scrape_player(url)
        if data:
            records.append(data)
    return pd.DataFrame(records)

# ======================
# Example run
# ======================
# Example DataFrame with URLs (replace with your df_with_urls)
df_with_urls = generate_urls(players)

df_with_urls["URL"] = df_with_urls["Player Number"].apply(
    lambda x: f"https://squid-game.fandom.com/wiki/Player_{str(x).zfill(3)}_(33rd_Squid_Game)"
)

# Scrape
players_df = scrape_all_players(df_with_urls)

# Save with semicolon separator
players_df.to_csv("squid_game_players.csv", index=False, sep=";", encoding="utf-8-sig")
files.download("squid_game_players.csv")
