import requests
import time

class RaiderIOAPIClient:
    def __init__(self, region: str, access_key: str = None):
        self.base_url = "https://raider.io/api/v1/characters/profile"
        self.region = region
        self.access_key = access_key

    def get_mythic_plus_profile(self, realm_slug: str, character_name: str):
        params = {
            "region": self.region,
            "realm": realm_slug,
            "name": character_name,
            "fields": "mythic_plus_scores_by_season:current,mythic_plus_weekly_highest_level_runs"
        }

        if self.access_key:
            params["access_key"] = self.access_key

        attempt = 0
        while attempt < 2:  # Maximal 2 Versuche (Original + 1 Retry)
            response = requests.get(self.base_url, params=params)

            # Raider.IO Server Fehler oder Timeout
            if response.status_code >= 500 or "text/html" in response.headers.get("Content-Type", ""):
                if attempt == 0:
                    print(f"⚠️ Raider.IO server issue (attempt {attempt + 1}). Retrying in 2 seconds...")
                    time.sleep(2)
                    attempt += 1
                    continue
                else:
                    raise Exception(f"Raider.IO server error after retry: {response.status_code}: {response.text}")

            # Charakter nicht gefunden
            if response.status_code == 400:
                print(f"⚠️ Character {character_name}-{realm_slug} not found on Raider.IO. Default values will be used.")
                return {}

            response.raise_for_status()
            return response.json()

        raise Exception(f"Raider.IO failed after retries for {character_name}-{realm_slug}")
