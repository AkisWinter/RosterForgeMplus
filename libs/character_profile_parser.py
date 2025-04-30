import datetime

class CharacterProfileParser:
    def __init__(self, profile_data, keystone_data, raid_data, debug=False, keystone_reward_mapping=None, raid_reward_mapping=None, active_raid_name=None):
        self.profile_data = profile_data or {}
        self.keystone_data = keystone_data or {}
        self.raid_data = raid_data or {}
        self.debug = debug
        self.keystone_reward_mapping = keystone_reward_mapping or {
            20: 483,
            17: 480,
            14: 476,
            11: 473,
            8: 470,
            5: 467,
            0: 463
        }
        self.raid_reward_mapping = raid_reward_mapping or {
            "LFR": 450,
            "Normal": 463,
            "Heroic": 476,
            "Mythic": 489
        }
        self.active_raid_name = active_raid_name

    def extract_character_info(self):
        guild_name = self.profile_data.get('guild', {}).get('name')
        guild_realm = self.profile_data.get('guild', {}).get('realm', {}).get('name')
        full_guild_name = f"{guild_name}-{guild_realm}" if guild_name and guild_realm else None

        info = {
            'name': self.profile_data.get('name', 'Unknown'),
            'realm': self.profile_data.get('realm', {}).get('name', 'Unknown'),
            'level': self.profile_data.get('level', 0),
            'class_name': self.profile_data.get('character_class', {}).get('name', 'Unknown'),
            'equipped_item_level': self.profile_data.get('equipped_item_level', 0),
            'average_item_level': self.profile_data.get('average_item_level', 0),
            'mythic_plus_score': self._get_mythic_plus_score(),
            'achievement_points': self.profile_data.get('achievement_points', 0),
            'vault_rewards': self._get_mplus_vault_rewards(),
            'raid_rewards': self._get_raid_vault_rewards(),
            'guild': full_guild_name
        }

        if self.debug:
            self.debug_print(info)

        return info

    def _get_mythic_plus_score(self):
        if 'mythic_plus_scores_by_season' in self.keystone_data:
            season_scores = self.keystone_data['mythic_plus_scores_by_season']
            if season_scores and isinstance(season_scores, list):
                return round(season_scores[0].get('scores', {}).get('all', 0), 1)
        elif 'current_mythic_rating' in self.keystone_data:
            return round(self.keystone_data.get('current_mythic_rating', {}).get('rating', 0), 1)
        return 0

    def _get_mplus_vault_rewards(self):
        vault = []
        if 'mythic_plus_weekly_highest_level_runs' in self.keystone_data:
            best_runs = self.keystone_data.get('mythic_plus_weekly_highest_level_runs', [])
        elif 'current_period' in self.keystone_data:
            best_runs = self.keystone_data.get('current_period', {}).get('best_runs', [])
        else:
            best_runs = []

        sorted_runs = sorted(best_runs, key=lambda x: x.get('mythic_level', 0) or x.get('keystone_level', 0), reverse=True)

        for i in range(3):
            if i < len(sorted_runs):
                keylevel = sorted_runs[i].get('mythic_level') or sorted_runs[i].get('keystone_level', 0)
                itemlevel = self._get_reward_item_level(keylevel)
                vault.append({"slot": i + 1, "key_level": keylevel, "item_level": itemlevel})
            else:
                vault.append({"slot": i + 1, "key_level": None, "item_level": None})

        return vault

    def _get_reward_item_level(self, keystone_level):
        for level, ilvl in sorted(self.keystone_reward_mapping.items(), reverse=True):
            if keystone_level >= level:
                return ilvl
        return None

    def _get_raid_vault_rewards(self):
        difficulty_order = ["Mythic", "Heroic", "Normal", "LFR"]
        boss_kills = {difficulty: 0 for difficulty in difficulty_order}

        if not self.active_raid_name:
            return [{"slot": i+1, "item_level": None} for i in range(3)]

        for expansion in self.raid_data.get('expansions', []):
            for instance in expansion.get('instances', []):
                if instance.get('instance', {}).get('name') == self.active_raid_name:
                    for mode in instance.get('modes', []):
                        difficulty = mode.get('difficulty', {}).get('name')
                        if difficulty in difficulty_order:
                            encounters = mode.get('progress', {}).get('encounters', [])
                            for encounter in encounters:
                                if encounter.get('completed_count', 0) > 0:
                                    boss_kills[difficulty] += 1

        vault = []
        required_kills = [2, 4, 6]

        for kills_needed in required_kills:
            for difficulty in difficulty_order:
                if boss_kills[difficulty] >= kills_needed:
                    ilvl = self.raid_reward_mapping.get(difficulty)
                    vault.append({"slot": len(vault)+1, "item_level": ilvl})
                    break
            else:
                vault.append({"slot": len(vault)+1, "item_level": None})

        return vault

    def debug_print(self, data):
        print("\nCharacter Profile Summary:")
        for key, value in data.items():
            print(f"{key}: {value}")