#! python3

# region Modules
import time, json, requests
import logging, os, sys
from datetime import datetime

from prometheus_client import start_http_server, REGISTRY, PROCESS_COLLECTOR, PLATFORM_COLLECTOR, Gauge, Enum
# endregion Modules

RUNESCAPE_USERNAME     = os.environ.get('RUNESCAPE_USERNAME', '')
RSRME_ACTIVITIES       = os.environ.get('RSRME_ACTIVITIES', 20) # 20 is max?
RSRME_LOG_TYPE         = os.environ.get('RSRME_LOG_TYPE', 'text') # text or details
RSRME_INTERVAL_MINUTES = int(os.environ.get('RSRME_INTERVAL_MINUTES', 30))

PROMETHEUS_PORT    = int(os.environ.get('PROMETHEUS_PORT', 8080))
LOKI_URL           = os.environ.get('LOKI_URL', 'http://loki:3100')


class App():
    RUNEMETRICS_PROFILE_URL = f'https://apps.runescape.com/runemetrics/profile/profile?user={RUNESCAPE_USERNAME}&activities={RSRME_ACTIVITIES}'
    METRICS = {}
    SKILL_ID_MAP = {
        0: 'Attack',
        1: 'Defence',
        2: 'Strength',
        3: 'Constitution',
        4: 'Ranged',
        5: 'Prayer',
        6: 'Magic',
        7: 'Cooking',
        8: 'Woodcutting',
        9: 'Fletching',
        10: 'Fishing',
        11: 'Firemaking',
        12: 'Crafting',
        13: 'Smithing',
        14: 'Mining',
        15: 'Herblore',
        16: 'Agility',
        17: 'Thieving',
        18: 'Slayer',
        19: 'Farming',
        20: 'Runecrafting',
        21: 'Hunter',
        22: 'Construction',
        23: 'Summoning',
        24: 'Dungeoneering',
        25: 'Divination',
        26: 'Invention',
        27: 'Archaeology',
        28: 'Necromancy'
    }

    def __init__(self) -> None:
        if RUNESCAPE_USERNAME == '':
            logging.error('RUNESCAPE_USERNAME is not set')
            sys.exit(1)

        REGISTRY.unregister(PROCESS_COLLECTOR)
        REGISTRY.unregister(PLATFORM_COLLECTOR)
        REGISTRY.unregister(REGISTRY._names_to_collectors['python_gc_objects_collected_total'])

        self.METRICS['rs3_total_xp']    = Gauge('rs3_total_xp',    'Total XP',        ['username'])
        self.METRICS['rs3_total_level'] = Gauge('rs3_total_level', 'Total Level',     ['username'])
        self.METRICS['rs3_total_rank']  = Gauge('rs3_total_rank',  'Total Rank',      ['username'])
        self.METRICS['rs3_skill_xp']    = Gauge('rs3_skill_xp',    'XP per skill',    ['username', 'skill'])
        self.METRICS['rs3_skill_level'] = Gauge('rs3_skill_level', 'Level per skill', ['username', 'skill'])
        self.METRICS['rs3_skill_rank']  = Gauge('rs3_skill_rank',  'Rank per skill',  ['username', 'skill'])

        self.METRICS['rs3_logged_in']    = Enum('rs3_logged_in',     'Logged In',    ['username'], states=['true', 'false'])
        self.METRICS['rs3_combat_level'] = Gauge('rs3_combat_level', 'Combat Level', ['username'])

        self.METRICS['rs3_quests_notstarted'] = Gauge('rs3_quests_notstarted', 'Quests Not Started', ['username'])
        self.METRICS['rs3_quests_started']    = Gauge('rs3_quests_started',    'Quests Started',     ['username'])
        self.METRICS['rs3_quests_complete']   = Gauge('rs3_quests_complete',   'Quests Complete',    ['username'])

    def run(self) -> None:
        start_http_server(PROMETHEUS_PORT)
        print('Prometheus started')

        self.updateMetrics()
        print('Initial logs loaded')

        while True:
            time.sleep(60 * RSRME_INTERVAL_MINUTES)
            self.updateMetrics()

    def updateMetrics(self) -> None:
        profileData = self.getProfileData()

        #region Update Prometheus Metrics
        self.METRICS['rs3_total_xp'].labels(username=RUNESCAPE_USERNAME).set(profileData['totalxp'])
        self.METRICS['rs3_total_level'].labels(username=RUNESCAPE_USERNAME).set(profileData['totalskill'])
        self.METRICS['rs3_total_rank'].labels(username=RUNESCAPE_USERNAME).set(int(profileData['rank'].replace(',', '')))

        for skill in profileData['skillvalues']:
            skillName = self.SKILL_ID_MAP[skill['id']]
            self.METRICS['rs3_skill_xp'].labels(username=RUNESCAPE_USERNAME, skill=skillName).set(skill['xp'])
            self.METRICS['rs3_skill_level'].labels(username=RUNESCAPE_USERNAME, skill=skillName).set(skill['level'])
            self.METRICS['rs3_skill_rank'].labels(username=RUNESCAPE_USERNAME, skill=skillName).set(skill['rank'])

        self.METRICS['rs3_logged_in'].labels(username=RUNESCAPE_USERNAME).state(profileData['loggedIn'])
        self.METRICS['rs3_combat_level'].labels(username=RUNESCAPE_USERNAME).set(profileData['combatlevel'])

        self.METRICS['rs3_quests_notstarted'].labels(username=RUNESCAPE_USERNAME).set(profileData['questsnotstarted'])
        self.METRICS['rs3_quests_started'].labels(username=RUNESCAPE_USERNAME).set(profileData['questsstarted'])
        self.METRICS['rs3_quests_complete'].labels(username=RUNESCAPE_USERNAME).set(profileData['questscomplete'])
        #endregion Update Prometheus Metrics

        # #region Send Activities to Loki
        logs = []
        for activity in profileData['activities']:
            logs.append([
                str(int(datetime.strptime(activity['date'], "%d-%b-%Y %H:%M").timestamp() * 1_000_000_000)),
                activity[RSRME_LOG_TYPE]
            ])
        self.sendToLoki(logs)
        # #endregion Send Activities to Loki

    def sendToLoki(self, logs) -> None:
        payload = {
            'streams': [{
                'stream': { 'job':  'runescape3', 'username': RUNESCAPE_USERNAME},
                'values': logs
            }]
        }

        response = requests.post(f"{LOKI_URL}/loki/api/v1/push", data=json.dumps(payload), headers={ 'Content-type': 'application/json' })
        if response.status_code != 204:
            logging.error(f"Error sending log to Loki: {response.status_code} - {response.text}")

    def getProfileData(self) -> dict:
        try:
            res = requests.get(self.RUNEMETRICS_PROFILE_URL)
            res.raise_for_status()
            return res.json()
        except Exception as e:
            print(f"[ERROR] RuneMetrics fetch failed: {e}")
            return {}

try:
    app = App()
    app.run()

except KeyboardInterrupt:
    sys.exit(0) # Remove traceback from Ctrl+C
