import requests
import base64
import datetime

class BlizzardAPIClient:
    def __init__(self, client_id, client_secret, region, locale="en_US"):
        self.client_id = client_id
        self.client_secret = client_secret
        self.region = region
        self.locale = locale
        self.access_token = self._get_access_token()

    def _get_access_token(self):
        token_url = f"https://{self.region}.battle.net/oauth/token"
        auth = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
        headers = {"Authorization": f"Basic {auth}"}
        data = {"grant_type": "client_credentials"}
        response = requests.post(token_url, headers=headers, data=data)
        response.raise_for_status()
        return response.json()['access_token']

    def _get(self, url, params=None):
        headers = {"Authorization": f"Bearer {self.access_token}"}
        if params is None:
            params = {}
        params.update({"namespace": f"profile-{self.region}", "locale": self.locale})
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()

    def get_guild_roster(self, realm_slug, guild_name):
        url = f"https://{self.region}.api.blizzard.com/data/wow/guild/{realm_slug}/{guild_name}/roster"
        data = self._get(url)
        return data.get('members', [])

    def get_character_profile(self, realm_slug, character_name):
        url = f"https://{self.region}.api.blizzard.com/profile/wow/character/{realm_slug}/{character_name}"
        return self._get(url)

    def get_mythic_keystone_profile(self, realm_slug, character_name):
        url = f"https://{self.region}.api.blizzard.com/profile/wow/character/{realm_slug}/{character_name}/mythic-keystone-profile"
        return self._get(url)

    def get_character_raid_profile(self, realm_slug, character_name):
        url = f"https://{self.region}.api.blizzard.com/profile/wow/character/{realm_slug}/{character_name}/encounters/raids"
        return self._get(url)

# Example usage:
# client = BlizzardAPIClient(client_id="your_client_id", client_secret="your_client_secret", region="eu")
# roster = client.get_guild_roster("realm-slug", "guild-name")
# print(roster)