import time
import urllib.parse
import urllib.request, urllib.error
import json
import ssl
import datetime


RIOT_API_KEY = str()

api_calls = 0
time_app = datetime.datetime.now()

regions =   ['BR1', 'EUN1', 'EUW1', 'JP1', 'KR', 'LA1', 'LA2', 'NA1', 'OC1', 'RU', 'TR1']
clusters =  ['AMERICAS', 'ASIA', 'EUROPE', 'ESPORTS']
queues =    ['RANKED_SOLO_5x5', 'RANKED_FLEX_SR', 'RANKED_FLEX_TT']
tiers =     ['DIAMOND', 'PLATINUM', 'GOLD', 'SILVER', 'BRONZE', 'IRON']
divisions = ['I', 'II', 'III', 'IV']

def to_url_base(region, request):
    """ returns a base url with data to be replaced with attributes
    syntax be like: https://<region|cluster>.api.riotgames.com<request>/<attributes>?api_key=<api_key>
    :param region: LOL server or cluster that goes before the api.riotgames.com web-page
    :param request: riot API call template that goes after api.riotgames.com. web-page
    :return: url with location and request added. Request information still needs to be filled
    """

    url_region = 'https://' + region + '.api.riotgames.com'

    intersection = '?api_key='
    connection = intersection + RIOT_API_KEY

    url_base = url_region + request + connection
    return url_base

def attribute_formatter(attribute):
    """ translate non-alphabetic chars and 'spaces' to a URL applicable format
    :param attribute: text string that may contain not url compatible chars (e.g. ' 무작위의')
    :return: text string with riot API compatible url encoding (e.g. %20%EB%AC%B4%EC%9E%91%EC%9C%84%EC%9D%98)
    """

    tempdict = {'': attribute}
    formatted = urllib.parse.urlencode(tempdict)[1:].replace('+', '%20')
    return formatted

def api_call(url, rate_limiting = True):
    """ ignores SSL errors, calls the API and returns a JSON
    :param url: riot API call url to connect to and retrieve its returning JSON
    :param rate_limiting:  establishes if the call should be counted for the rate-limiter, True by default
    :return: JSON object retrieved from riot API call
    """

    # Limits rating at 100 calls every 120 seconds (modifiable though top and limit_interval). Intended for API dev keys.
    global api_calls
    global time_app
    top = 100
    limit_interval = 120
    if rate_limiting:
        api_calls += 1
        time_diff = (datetime.datetime.now() - time_app).total_seconds()
        if api_calls >= top and time_diff < limit_interval:
            print('429 potential error on next API call')
            print(top, 'API calls per', limit_interval, 'secs rate limit exceeded, sleeping...')
            print('Rate limits can be edited by changing the loliglio.top and loliglio.limit_interval variables')
            # Restarts counter
            api_calls = 1
            time_app = datetime.datetime.now()

            time.sleep(limit_interval)
    # Ignore SSL certificate errors
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    # Waits an interval in case 429 error happened during API call
    # For other errors prints error response and exits
    try:
        uh = urllib.request.urlopen(url, context=ctx)
    except urllib.error.HTTPError as e:
        if e.__dict__['code'] == 429:
            print('429 error happened during API call')
            print(top, 'API calls per', limit_interval, 'secs rate limit exceeded, sleeping...')
            # Restarts counter
            api_calls = 1
            time.sleep(limit_interval)
        else:
            print(e.__dict__)
            exit(e.__dict__['code'])
        uh = urllib.request.urlopen(url, context=ctx)

    data_str = uh.read().decode()
    data_json = json.loads(data_str)
    return data_json

class Account:
    """ Allows accessing to the puuid, gameName and tagLine of a LOL account
    official information at: https://developer.riotgames.com/apis#account-v1
    """

    @staticmethod
    def by_puuid(clusterId, puuid, get_url=False):
        """ Get account by puuid
        :param clusterId: riot cluster ID. Accepted values: 0-2(inclusive) respective to 'AMERICAS', 'ASIA' & 'EUROPE'
        :param puuid: Public User ID's are globally unique. Different APIs use different IDs
        :param get_url: When true, don't make an API call and returns the url connection
        :return: JSON object retrieved from riot API call (or link when get_url is True)
        """

        url_base = to_url_base(clusters[clusterId], '/riot/account/v1/accounts/by-puuid/{puuid}')
        url = url_base.replace('{puuid}', attribute_formatter(puuid))
        if get_url: return url
        return api_call(url)

    @staticmethod
    def by_riot_id(clusterId, gameName, tagLine, get_url=False):
        """ Get account by riot id
        :param clusterId: riot cluster ID. Accepted values: 0-2(inclusive) respective to 'AMERICAS', 'ASIA' & 'EUROPE'
        :param gameName: Name as shown in the League Client (can contain not-alphabetic chars)
        :param tagLine: Tag line as shown in the League Client
        :param get_url: When true, don't make an API call and returns the url connection
        :return: JSON object retrieved from riot API call (or link when get_url is True)
        """

        url_base = to_url_base(clusters[clusterId], '/riot/account/v1/accounts/by-riot-id/{gameName}/{tagLine}')
        url = url_base.replace('{gameName}', attribute_formatter(gameName)).replace('{tagLine}', attribute_formatter(tagLine))
        if get_url: return url
        return api_call(url)

class ChampionMastery:
    """ Allows accessing the score and ChampionMasteryDto of every / a-single champion
    official information at: https://developer.riotgames.com/apis#champion-mastery-v4

    ChampionMasteryDto - This object contains single Champion Mastery information for player and champion combination.
    NAME                            | DATA TYPE    | DESCRIPTION
    --------------------------------|-----------|----------------------------------------------------------------------
    championPointsUntilNextLevel    | long      | Number of points needed to achieve next level. Zero if player reached maximum champion level for this champion.
    chestGranted                    | boolean   |    Is chest granted for this champion or not in current season.
    championId                        | long      | Champion ID for this entry.
    lastPlayTime                    | long      | Last time this champion was played by this player - in Unix milliseconds time format.
    championLevel                   | int       | Champion level for specified player and champion combination.
    summonerId                        | string    | Summoner ID for this entry. (Encrypted)
    championPoints                  | int       | Total number of champion points for this player and champion combination - they are used to determine championLevel.
    championPointsSinceLastLevel    | long      | Number of points earned since current level has been achieved.
    tokensEarned                    | int       | The token earned for this champion at the current championLevel. When the championLevel is advanced the tokensEarned resets to 0.
    """

    @staticmethod
    def by_summoner(regionId, encryptedSummonerId, get_url=False):
        """ Get all champion mastery entries sorted by number of champion points descending,
        :param regionId: LOL server ID. Accepted values: 0-11(inclusive) for 'BR1', 'EUN1', 'EUW1', 'JP1', 'KR', 'LA1', 'LA2', 'NA1', 'OC1', 'RU' & 'TR1'
        :param encryptedSummonerId: Summoner IDs are only unique per region. Different APIs use different IDs
        :param get_url: When true, don't make an API call and returns the url connection
        :return: JSON object retrieved from riot API call (or link when get_url is True)
        """

        url_base = to_url_base(regions[regionId], '/lol/champion-mastery/v4/champion-masteries/by-summoner/{encryptedSummonerId}')
        url = url_base.replace('{encryptedSummonerId}', attribute_formatter(encryptedSummonerId))
        if get_url: return url
        return api_call(url)

    @staticmethod
    def by_summoner_champion(regionId, encryptedSummonerId, championId, get_url=False):
        """ Get a champion mastery by player ID and champion ID.
        :param regionId: LOL server ID. Accepted values: 0-11(inclusive) for 'BR1', 'EUN1', 'EUW1', 'JP1', 'KR', 'LA1', 'LA2', 'NA1', 'OC1', 'RU' & 'TR1'
        :param encryptedSummonerId: Summoner IDs are only unique per region. Different APIs use different IDs
        :param championId: Integer that represents the champion you want to retrieve (e.g. 1 -> Annie)
        :param get_url: When true, don't make an API call and returns the url connection
        :return: JSON object retrieved from riot API call (or link when get_url is True)
        """

        championId = str(championId)
        url_base = to_url_base(regions[regionId], '/lol/champion-mastery/v4/champion-masteries/by-summoner/{encryptedSummonerId}/by-champion/{championId}')
        url = url_base.replace('{encryptedSummonerId}', attribute_formatter(encryptedSummonerId)).replace('{championId}', attribute_formatter(championId))
        if get_url: return url
        return api_call(url)

    @staticmethod
    def score_by_summoner(regionId, encryptedSummonerId, get_url=False):
        """ Get a player's total champion mastery score, which is the sum of individual champion mastery levels.
        :param regionId: LOL server ID. Accepted values: 0-11(inclusive) for 'BR1', 'EUN1', 'EUW1', 'JP1', 'KR', 'LA1', 'LA2', 'NA1', 'OC1', 'RU' & 'TR1'
        :param encryptedSummonerId: Summoner IDs are only unique per region. Different APIs use different IDs
        :param get_url: When true, don't make an API call and returns the url connection
        :return: JSON object retrieved from riot API call (or link when get_url is True)
        """

        url_base = to_url_base(regions[regionId], '/lol/champion-mastery/v4/scores/by-summoner/{encryptedSummonerId}')
        url = url_base.replace('{encryptedSummonerId}', attribute_formatter(encryptedSummonerId))
        if get_url: return url
        return api_call(url)

class Champion:
    """ Access to current champion rotations by region from Riot API and champion information from DataDragon
    official information at: https://developer.riotgames.com/apis#champion-v3
    DataDragon champ info to-date (02-22): 'http://ddragon.leagueoflegends.com/cdn/'12.4.1'/data/de_DE/champion.json'
    """

    @staticmethod
    def champion_rotations(regionId, get_url=False):
        """ Returns champion rotations, including free-to-play and low-level free-to-play rotations
        :param regionId: LOL server ID. Accepted values: 0-11(inclusive) for 'BR1', 'EUN1', 'EUW1', 'JP1', 'KR', 'LA1', 'LA2', 'NA1', 'OC1', 'RU' & 'TR1'
        :param get_url: When true, don't make an API call and returns the url connection
        :return: JSON object retrieved from riot API call (or link when get_url is True)
        """

        url = to_url_base(regions[regionId], '/lol/platform/v3/champion-rotations')
        if get_url: return url
        return api_call(url)

    @staticmethod
    def champions(version, get_url=False):
        """ Returns all available champion data from DataDragon at the specified version
        :param version: String containing the current version of LOL (e.g. '12.4.1' to this date)
        :param get_url: When true, don't make a DataDragon API call and returns the url connection
        :return: JSON object retrieved from DataDragon API call (or link when get_url is True)
        """
        url = 'http://ddragon.leagueoflegends.com/cdn/' + version + '/data/de_DE/champion.json'
        if get_url: return url
        return api_call(url, rate_limiting=False)

    @staticmethod
    def names(version, get_url=False):
        """ Returns a list of strings containing each champion's name (Wukong name is 'Wukong')
        :param version: String containing the current version of LOL (e.g. '12.4.1' to this date)
        :param get_url: When true, don't make a DataDragon API call and returns the url connection
        :return: JSON object retrieved from DataDragon API call (or link when get_url is True)
        """
        url = 'http://ddragon.leagueoflegends.com/cdn/' + version + '/data/de_DE/champion.json'
        if get_url: return url
        champ_info = api_call(url, rate_limiting=False)
        ids = list()
        for item in champ_info['data']:
            ids.append(item)
        return_info = list()
        for i in range(len(champ_info['data'])):
            return_info.append(champ_info['data'][ids[i]]['name'])
        return return_info

    @staticmethod
    def ids(version, get_url=False):
        """ Returns a list of strings containing each champion's id (Wukong name is 'moneyking')
        :param version: String containing the current version of LOL (e.g. '12.4.1' to this date)
        :param get_url: When true, don't make a DataDragon API call and returns the url connection
        :return: JSON object retrieved from DataDragon API call (or link when get_url is True)
        """
        url = 'http://ddragon.leagueoflegends.com/cdn/' + version + '/data/de_DE/champion.json'
        if get_url: return url
        champ_info = api_call(url, rate_limiting=False)
        ids = list()
        for item in champ_info['data']:
            ids.append(item)
        return_info = list()
        for i in range(len(champ_info['data'])):
            return_info.append(champ_info['data'][ids[i]]['id'])
        return return_info

    @staticmethod
    def keys(version, get_url=False):
        """ Returns a list of ints containing each champion's key
        :param version: String containing the current version of LOL (e.g. '12.4.1' to this date)
        :param get_url: When true, don't make a DataDragon API call and returns the url connection
        :return: JSON object retrieved from DataDragon API call (or link when get_url is True)
        """
        url = 'http://ddragon.leagueoflegends.com/cdn/' + version + '/data/de_DE/champion.json'
        if get_url: return url
        champ_info = api_call(url, rate_limiting=False)
        ids = list()
        for item in champ_info['data']:
            ids.append(item)
        return_info = list()
        for i in range(len(champ_info['data'])):
            return_info.append(champ_info['data'][ids[i]]['key'])
        return return_info

    @staticmethod
    def by_name(version, championName, get_url=False):
        """ Returns information of the champion specified. P.D. Wukong name is 'Wukong'
        :param version: String containing the current version of LOL (e.g. '12.4.1' to this date)
        :param championName: text string containing a champion name. P.D. Wukong champion's name is 'Wukong'
        :param get_url: When true, don't make a DataDragon API call and returns the url connection
        :return: JSON object retrieved from DataDragon API call (or link when get_url is True)
        """
        url = 'http://ddragon.leagueoflegends.com/cdn/' + version + '/data/de_DE/champion.json'
        if get_url: return url
        champ_info = api_call(url, rate_limiting=False)
        ids = list()
        for item in champ_info['data']:
            ids.append(item)
        for i in range(len(champ_info['data'])):
            if champ_info['data'][ids[i]]['name'] == championName:
                return champ_info['data'][ids[i]]
        return 404

    @staticmethod
    def by_id(version, championId, get_url=False):
        """ Returns information of the champion specified. P.D. Wukong id is 'moneyking'
        :param version: String containing the current version of LOL (e.g. '12.4.1' to this date)
        :param championId: text string containing a champion ID. P.D. Wukong champion's ID is 'moneyking'
        :param get_url: When true, don't make a DataDragon API call and returns the url connection
        :return: JSON object retrieved from DataDragon API call (or link when get_url is True)
        """
        url = 'http://ddragon.leagueoflegends.com/cdn/' + version + '/data/de_DE/champion.json'
        if get_url: return url
        champ_info = api_call(url, rate_limiting=False)
        ids = list()
        for item in champ_info['data']:
            ids.append(item)
        for i in range(len(champ_info['data'])):
            if champ_info['data'][ids[i]]['id'] == championId:
                return champ_info['data'][ids[i]]
        return 404

    @staticmethod
    def by_key(version, championKey, get_url=False):
        """ Returns information of the champion specified
        :param version: String containing the current version of LOL (e.g. '12.4.1' to this date)
        :param championKey: numerical value containing a champion key.
        :param get_url: When true, don't make a DataDragon API call and returns the url connection
        :return: JSON object retrieved from DataDragon API call (or link when get_url is True)
        """
        championKey = str(championKey)
        url = 'http://ddragon.leagueoflegends.com/cdn/' + version + '/data/de_DE/champion.json'
        if get_url: return url
        champ_info = api_call(url, rate_limiting=False)
        ids = list()
        for item in champ_info['data']:
            ids.append(item)
        for i in range(len(champ_info['data'])):
            if champ_info['data'][ids[i]]['key'] == championKey:
                return champ_info['data'][ids[i]]
        return 404

class Clash:
    """ Allow access to all clash information: PlayerDto, TeamDto, TournamentDto & TournamentPhaseDto
    official information at: https://developer.riotgames.com/apis#clash-v1

    PlayerDto - Contains a player clash related information:
    NAME        | DATA TYPE | DESCRIPTION
    ------------|-----------|-----------
    summonerId  | string    |
    teamId      | string    |
    position    | string    | (Legal values: UNSELECTED, FILL, TOP, JUNGLE, MIDDLE, BOTTOM, UTILITY)
    role        | string    | (Legal values: CAPTAIN, MEMBER)

    TeamDto - Contains a team clash related information:
    NAME            | DATA TYPE       | DESCRIPTION
    ----------------|-----------------|-----------------
    id              | string          |
    tournamentId    | int             |
    name            | string          |
    iconId          | int             |
    tier            | int             |
    captain         | string          | Summoner ID of the team captain.
    abbreviation    | string          |
    players         | List[PlayerDto] | Team members.

    TournamentDto - Contains clash tournament information:
    NAME                | DATA TYPE                   | DESCRIPTION
    --------------------|-----------------------------|-------------------
    id                  | int                         |
    themeId             | int                         |
    nameKey             | string                      |
    nameKeySecondary    | string                      |
    schedule            | List[TournamentPhaseDto]    | Tournament phase.

    TournamentPhaseDto - Contains a clash tournament phase information:
    NAME                | DATA TYPE
    --------------------|--------------------
    id                  | int
    registrationTime    | long
    startTime           | long
    cancelled           | boolean
    """

    @staticmethod
    def players_by_summoner(regionId, summonerId, get_url=False):
        """ Get players (List[PlayerDto]) by summoner ID.
        :param regionId: LOL server ID. Accepted values: 0-11(inclusive) for 'BR1', 'EUN1', 'EUW1', 'JP1', 'KR', 'LA1', 'LA2', 'NA1', 'OC1', 'RU' & 'TR1'
        :param summonerId: Summoner IDs are only unique per region. Different APIs use different IDs
        :param get_url: When true, don't make an API call and returns the url connection
        :return: JSON object retrieved from riot API call (or link when get_url is True)
        """
        url_base = to_url_base(regions[regionId], '/lol/clash/v1/players/by-summoner/{summonerId}')
        url = url_base.replace('{summonerId}', attribute_formatter(summonerId))
        if get_url: return url
        return api_call(url)

    @staticmethod
    def teams(regionId, teamId, get_url=False):
        """ Get team (TeamDto) by ID.
        :param regionId: LOL server ID. Accepted values: 0-11(inclusive) for 'BR1', 'EUN1', 'EUW1', 'JP1', 'KR', 'LA1', 'LA2', 'NA1', 'OC1', 'RU' & 'TR1'
        :param teamId: unique value that identifies a team inside a Clash Tournament
        :param get_url: When true, don't make an API call and returns the url connection
        :return: JSON object retrieved from riot API call (or link when get_url is True)
        """
        teamId = str(teamId)
        url_base = to_url_base(regions[regionId], '/lol/clash/v1/teams/{teamId}')
        url = url_base.replace('{teamId}', attribute_formatter(teamId))
        if get_url: return url
        return api_call(url)

    @staticmethod
    def tournaments(regionId, get_url=False):
        """ Get all active or upcoming tournaments (List[TournamentDto]).
        :param regionId: LOL server ID. Accepted values: 0-11(inclusive) for 'BR1', 'EUN1', 'EUW1', 'JP1', 'KR', 'LA1', 'LA2', 'NA1', 'OC1', 'RU' & 'TR1'
        :param get_url: When true, don't make an API call and returns the url connection
        :return: JSON object retrieved from riot API call (or link when get_url is True)
        """
        url = to_url_base(regions[regionId], '/lol/clash/v1/tournaments')
        if get_url: return url
        return api_call(url)

    @staticmethod
    def tournament_by_team(regionId, teamId, get_url=False):
        """ Get tournament by team ID. (TournamentDto & TournamentPhaseDto)
        :param regionId: LOL server ID. Accepted values: 0-11(inclusive) for 'BR1', 'EUN1', 'EUW1', 'JP1', 'KR', 'LA1', 'LA2', 'NA1', 'OC1', 'RU' & 'TR1'
        :param teamId: unique value that identifies a team inside a Clash Tournament
        :param get_url: When true, don't make an API call and returns the url connection
        :return: JSON object retrieved from riot API call (or link when get_url is True)
        """
        url_base = to_url_base(regions[regionId], '/lol/clash/v1/tournaments/by-team/{teamId}')
        url = url_base.replace('{teamId}', attribute_formatter(teamId))
        if get_url: return url
        return api_call(url)

    @staticmethod
    def tournament_by_tournament_id(regionId, tournamentId, get_url=False):
        """ Get tournament by ID. (TournamentDto & TournamentPhaseDto)
        :param regionId: LOL server ID. Accepted values: 0-11(inclusive) for 'BR1', 'EUN1', 'EUW1', 'JP1', 'KR', 'LA1', 'LA2', 'NA1', 'OC1', 'RU' & 'TR1'
        :param tournamentId: numerical value that identifies a tournament inside a region
        :param get_url: When true, don't make an API call and returns the url connection
        :return: JSON object retrieved from riot API call (or link when get_url is True)
        """
        tournamentId = str(tournamentId)
        url_base = to_url_base(regions[regionId], '/lol/clash/v1/tournaments/{tournamentId}')
        url = url_base.replace('{tournamentId}', attribute_formatter(tournamentId))
        if get_url: return url
        return api_call(url)

class League:
    """ Allows request for league information LeagueListDTO and entries LeagueItemDTO
    official information at: https://developer.riotgames.com/apis#league-v4

    LeagueListDTO - Contains a league information
    NAME            | DATA TYPE
    ----------------|----------------
    leagueId        | string
    entries         | List[LeagueItemDTO]
    tier            | string
    name            | string
    queue           | string

    LeagueItemDTO - Contains a league member information, entries of  LeagueListDTO
    NAME            | DATA TYPE     | DESCRIPTION
    ----------------|---------------|----------------
    freshBlood      | boolean       |
    wins            | int           | Winning team on Summoners Rift.
    summonerName    | string        |
    miniSeries      | MiniSeriesDTO |
    inactive        | boolean       |
    veteran         | boolean       |
    hotStreak       | boolean       |
    rank            | string        |
    leaguePoints    | int           |
    losses          | int           | Losing team on Summoners Rift.
    summonerId      | string        | Player's encrypted summonerId.

    MiniSeriesDTO - Mini series leagues information
    ----------------|---------------
    NAME            | DATA TYPE
    losses          | int
    progress        | string
    target          | int
    wins            | int
    """
    class EXP:
        @staticmethod
        def entries(regionId, queueId, tierId, divisionId, get_url=False):
            """ Get all the league entries. (Set[LeagueEntryDTO])
            This new endpoint also supports the apex tiers (Challenger, Grandmaster, and Master)
            :param regionId: LOL server ID. Accepted values: 0-11(inclusive) for 'BR1', 'EUN1', 'EUW1', 'JP1', 'KR', 'LA1', 'LA2', 'NA1', 'OC1', 'RU' & 'TR1'
            :param queueId: LOL queue ID. Accepted values: 0-2(inclusive) for 'RANKED_SOLO_5x5', 'RANKED_FLEX_SR' & 'RANKED_FLEX_TT'
            :param tierId: LOL tier ID. Accepted values: 0-5(inclusive) for 'DIAMOND', 'PLATINUM', 'GOLD', 'SILVER', 'BRONZE' & 'IRON'
            :param divisionId: LOL division ID. Accepted values: 0-3(inclusive) for 'I', 'II', 'III', 'IV'
            :param get_url: When true, don't make an API call and returns the url connection
            :return: JSON object retrieved from riot API call (or link when get_url is True)
            """
            url_base = to_url_base(regions[regionId], '/lol/league-exp/v4/entries/{queue}/{tier}/{division}')
            url = url_base.replace('{queue}', attribute_formatter(queues[queueId])).replace('{tier}', attribute_formatter(tiers[tierId])).replace('{division}', attribute_formatter(divisions[divisionId]))
            if get_url: return url
            return api_call(url)

    @staticmethod
    def challenger_leagues_by_queue(regionId, queueId, get_url=False):
        """ Get the challenger league for given queue. (LeagueListDTO)
        :param regionId: LOL server ID. Accepted values: 0-11(inclusive) for 'BR1', 'EUN1', 'EUW1', 'JP1', 'KR', 'LA1', 'LA2', 'NA1', 'OC1', 'RU' & 'TR1'
        :param queueId: LOL queue ID. Accepted values: 0-2(inclusive) for 'RANKED_SOLO_5x5', 'RANKED_FLEX_SR' & 'RANKED_FLEX_TT'
        :param get_url: When true, don't make an API call and returns the url connection
        :return: JSON object retrieved from riot API call (or link when get_url is True)
        """
        url_base = to_url_base(regions[regionId], '/lol/league/v4/challengerleagues/by-queue/{queue}')
        url = url_base.replace('{queue}', attribute_formatter(queues[queueId]))
        if get_url: return url
        return api_call(url)

    @staticmethod
    def master_leagues_by_queue(regionId, queueId, get_url=False):
        """ Get the master league for given queue. (LeagueListDTO)
        :param regionId: LOL server ID. Accepted values: 0-11(inclusive) for 'BR1', 'EUN1', 'EUW1', 'JP1', 'KR', 'LA1', 'LA2', 'NA1', 'OC1', 'RU' & 'TR1'
        :param queueId: LOL queue ID. Accepted values: 0-2(inclusive) for 'RANKED_SOLO_5x5', 'RANKED_FLEX_SR' & 'RANKED_FLEX_TT'
        :param get_url: When true, don't make an API call and returns the url connection
        :return: JSON object retrieved from riot API call (or link when get_url is True)
        """
        url_base = to_url_base(regions[regionId], '/lol/league/v4/masterleagues/by-queue/{queue}')
        url = url_base.replace('{queue}', attribute_formatter(queues[queueId]))
        if get_url: return url
        return api_call(url)

    @staticmethod
    def grandmaster_by_queue(regionId, queueId, get_url=False):
        """ Get the grandmaster league of a specific queue. (LeagueListDTO)
        :param regionId: LOL server ID. Accepted values: 0-11(inclusive) for 'BR1', 'EUN1', 'EUW1', 'JP1', 'KR', 'LA1', 'LA2', 'NA1', 'OC1', 'RU' & 'TR1'
        :param queueId: LOL queue ID. Accepted values: 0-2(inclusive) for 'RANKED_SOLO_5x5', 'RANKED_FLEX_SR' & 'RANKED_FLEX_TT'
        :param get_url: When true, don't make an API call and returns the url connection
        :return: JSON object retrieved from riot API call (or link when get_url is True)
        """
        url_base = to_url_base(regions[regionId], '/lol/league/v4/grandmasterleagues/by-queue/{queue}')
        url = url_base.replace('{queue}', attribute_formatter(queues[queueId]))
        if get_url: return url
        return api_call(url)

    @staticmethod
    def entries_by_summoner(regionId, encryptedSummonerId, get_url=False):
        """ Get league entries in all queues for a given summoner ID. (Set[LeagueEntryDTO])
        :param regionId: LOL server ID. Accepted values: 0-11(inclusive) for 'BR1', 'EUN1', 'EUW1', 'JP1', 'KR', 'LA1', 'LA2', 'NA1', 'OC1', 'RU' & 'TR1'
        :param encryptedSummonerId: Summoner IDs are only unique per region. Different APIs use different IDs
        :param get_url: get_url: When true, don't make an API call and returns the url connection
        :return: JSON object retrieved from riot API call (or link when get_url is True)
        """
        url_base = to_url_base(regions[regionId], '/lol/league/v4/entries/by-summoner/{encryptedSummonerId}')
        url = url_base.replace('{encryptedSummonerId}', attribute_formatter(encryptedSummonerId))
        if get_url: return url
        return api_call(url)

    @staticmethod
    def entries(regionId, queueId, tierId, divisionId, get_url=False):
        """ Get all the league entries (Set[LeagueEntryDTO]).
        :param regionId: LOL server ID. Accepted values: 0-11(inclusive) for 'BR1', 'EUN1', 'EUW1', 'JP1', 'KR', 'LA1', 'LA2', 'NA1', 'OC1', 'RU' & 'TR1'
        :param queueId: LOL queue ID. Accepted values: 0-2(inclusive) for 'RANKED_SOLO_5x5', 'RANKED_FLEX_SR' & 'RANKED_FLEX_TT'
        :param tierId: LOL tier ID. Accepted values: 0-5(inclusive) for 'DIAMOND', 'PLATINUM', 'GOLD', 'SILVER', 'BRONZE' & 'IRON'
        :param divisionId: LOL division ID. Accepted values: 0-3(inclusive) for 'I', 'II', 'III', 'IV'
        :param get_url: When true, don't make an API call and returns the url connection
        :return: JSON object retrieved from riot API call (or link when get_url is True)
        """
        url_base = to_url_base(regions[regionId], '/lol/league/v4/entries/{queue}/{tier}/{division}')
        url = url_base.replace('{queue}', attribute_formatter(queues[queueId])).replace('{tier}', attribute_formatter(tiers[tierId])).replace('{division}', attribute_formatter(divisions[divisionId]))
        if get_url: return url
        return api_call(url)

    @staticmethod
    def leagues(regionId, leagueId, get_url=False):
        """ Get league with given ID, including inactive entries (LeagueListDTO).
        :param regionId: LOL server ID. Accepted values: 0-11(inclusive) for 'BR1', 'EUN1', 'EUW1', 'JP1', 'KR', 'LA1', 'LA2', 'NA1', 'OC1', 'RU' & 'TR1'
        :param leagueId: Division and queue for a specific region ID. (e.g. 'f3b585a2-8b09-3940-b3fc-d2e404f2a5c4' refers to LA2 Ranked_5x5 Grandmaster league)
        :param get_url: When true, don't make an API call and returns the url connection
        :return: JSON object retrieved from riot API call (or link when get_url is True)
        """
        url_base = to_url_base(regions[regionId], '/lol/league/v4/leagues/{leagueId}')
        url = url_base.replace('{leagueId}', attribute_formatter(leagueId))
        if get_url: return url
        return api_call(url)

class Status:
    """ Allows access to LOL platform status by region
    official information at: https://developer.riotgames.com/apis#lol-status-v4
    official information at: https://developer.riotgames.com/apis#lol-status-v3
    """
    class V3:
        @staticmethod
        def shard_data(regionId, get_url=False):
            """ Get League of Legends status for the given shard.
            This API was deprecated on Dec 11th, 2020. Please use lol-status-v4 as a replacement.
            :param regionId: LOL server ID. Accepted values: 0-11(inclusive) for 'BR1', 'EUN1', 'EUW1', 'JP1', 'KR', 'LA1', 'LA2', 'NA1', 'OC1', 'RU' & 'TR1'
            :param get_url: When true, don't make an API call and returns the url connection
            :return: JSON object retrieved from riot API call (or link when get_url is True)
            """
            url = to_url_base(regions[regionId], '/lol/status/v3/shard-data')
            if get_url: return url
            return api_call(url)
    class V4:
        @staticmethod
        def platform_data(regionId, get_url=False):
            """ Get League of Legends status for the given platform
            :param regionId: LOL server ID. Accepted values: 0-11(inclusive) for 'BR1', 'EUN1', 'EUW1', 'JP1', 'KR', 'LA1', 'LA2', 'NA1', 'OC1', 'RU' & 'TR1'
            :param get_url: When true, don't make an API call and returns the url connection
            :return: JSON object retrieved from riot API call (or link when get_url is True)
            """
            url = to_url_base(regions[regionId], '/lol/status/v4/platform-data')
            if get_url: return url
            return api_call(url)

class Match:
    """ Returns MatchDto
    official information at: https://developer.riotgames.com/apis#match-v5
    """

    @staticmethod
    def matches(matchId, get_url=False):
        """ Get a match by match id
        :param matchId: LOL match ID. Syntax contains <Region>_<NumericalSequence> (e.g. 'LA2_1138947703')
        :param get_url: When true, don't make an API call and returns the url connection
        :return: JSON object retrieved from riot API call (or link when get_url is True)
        """
        matchId = attribute_formatter(matchId)
        if matchId.startswith(regions[0]) or matchId.startswith(regions[5]) or matchId.startswith(
                regions[6]) or matchId.startswith(regions[7]) or matchId.startswith(regions[8]):
            clusterId = 0
        elif matchId.startswith(regions[3]) or matchId.startswith(regions[4]):
            clusterId = 1
        else:
            clusterId = 3
        url_base = to_url_base(clusters[clusterId], '/lol/match/v5/matches/{matchId}')
        url = url_base.replace('{matchId}', matchId)
        if get_url: return url
        return api_call(url)

    @staticmethod
    def matches_by_puuid(clusterId, puuid, get_url=False):
        """ Get a list of match ids by puuid
        :param clusterId: riot cluster ID. Accepted values: 0-2(inclusive) respective to 'AMERICAS', 'ASIA' & 'EUROPE'
        :param puuid: Public User ID's are globally unique. Different APIs use different IDs
        :param get_url: When true, don't make an API call and returns the url connection
        :return: JSON object retrieved from riot API call (or link when get_url is True)
        """
        # TODO : This API call can contain parameters, check: https://developer.riotgames.com/apis#match-v5/GET_getMatchIdsByPUUID
        url_base = to_url_base(clusters[clusterId], '/lol/match/v5/matches/by-puuid/{puuid}/ids')
        url = url_base.replace('{puuid}', attribute_formatter(puuid))
        if get_url: return url
        return api_call(url)

    @staticmethod
    def matches_timeline(matchId, get_url=False):
        """ Get a match timeline by match id
        :param matchId: LOL match ID. Syntax contains <Region>_<NumericalSequence> (e.g. 'LA2_1138947703')
        :param get_url: When true, don't make an API call and returns the url connection
        :return: JSON object retrieved from riot API call (or link when get_url is True)
        """
        matchId = attribute_formatter(matchId)
        # The AMERICAS routing value serves NA, BR, LAN, LAS, and OCE. The ASIA routing value serves KR and JP. The EUROPE routing value serves EUNE, EUW, TR, and RU.
        if matchId.startswith(regions[0]) or matchId.startswith(regions[5]) or matchId.startswith(
                regions[6]) or matchId.startswith(regions[7]) or matchId.startswith(regions[8]):
            clusterId = 0
        elif matchId.startswith(regions[3]) or matchId.startswith(regions[4]):
            clusterId = 1
        else:
            clusterId = 3
        url_base = to_url_base(clusters[clusterId], '/lol/match/v5/matches/{matchId}/timeline')
        url = url_base.replace('{matchId}', matchId)
        if get_url: return url
        return api_call(url)

class Spectator:
    """ Allows the request of information of a current game
    official information at: https://developer.riotgames.com/apis#match-v5
    """

    @staticmethod
    def active_games_by_summoner(regionId, encryptedSummonerId, get_url=False):
        """
        :param regionId: LOL server ID. Accepted values: 0-11(inclusive) for 'BR1', 'EUN1', 'EUW1', 'JP1', 'KR', 'LA1', 'LA2', 'NA1', 'OC1', 'RU' & 'TR1'
        :param encryptedSummonerId: Summoner IDs are only unique per region. Different APIs use different IDs
        :param get_url: When true, don't make an API call and returns the url connection
        :return: JSON object retrieved from riot API call (or link when get_url is True)
        """
        url_base = to_url_base(regions[regionId], '/lol/spectator/v4/active-games/by-summoner/{encryptedSummonerId}')
        url = url_base.replace('{encryptedSummonerId}', attribute_formatter(encryptedSummonerId))
        if get_url: return url
        return api_call(url)

    @staticmethod
    def featured_games(regionId, get_url=False):
        """
        :param regionId: LOL server ID. Accepted values: 0-11(inclusive) for 'BR1', 'EUN1', 'EUW1', 'JP1', 'KR', 'LA1', 'LA2', 'NA1', 'OC1', 'RU' & 'TR1'
        :param get_url: When true, don't make an API call and returns the url connection
        :return: JSON object retrieved from riot API call (or link when get_url is True)
        """
        url = to_url_base(regions[regionId], '/lol/spectator/v4/featured-games')
        if get_url: return url
        return api_call(url)

class Summoner:
    """ official information at: https://developer.riotgames.com/apis#summoner-v4
    Allows access to the information of a specific summoner. Returns a SummonerDTO
    
    NAME            | DATA TYPE  | DESCRIPTION
    ----------------|------------|----------------
    accountId       | string     | Encrypted account ID. Max length 56 characters.
    profileIconId   | int        | ID of the summoner icon associated with the summoner.
    revisionDate    | long       | Date summoner was last modified specified as epoch milliseconds. The following events will update this timestamp: summoner name change, summoner level change, or profile icon change.
    name            | string     | Summoner name.
    id              | string     | Encrypted summoner ID. Max length 63 characters.
    puuid           | string     | Encrypted PUUID. Exact length of 78 characters.
    summonerLevel   | long       | Summoner level associated with the summoner.
    """
    @staticmethod
    def by_account(regionId, encryptedAccountId, get_url=False):
        """ Get a summoner SummonerDTO by account ID
        :param regionId: LOL server ID. Accepted values: 0-11(inclusive) for 'BR1', 'EUN1', 'EUW1', 'JP1', 'KR', 'LA1', 'LA2', 'NA1', 'OC1', 'RU' & 'TR1'
        :param encryptedAccountId: Summoner IDs are only unique per region. Different APIs use different IDs
        :param get_url: When true, don't make an API call and returns the url connection
        :return: JSON object retrieved from riot API call (or link when get_url is True)
        """
        url_base = to_url_base(regions[regionId], '/lol/summoner/v4/summoners/by-account/{encryptedAccountId}')
        url = url_base.replace('{encryptedAccountId}', attribute_formatter(encryptedAccountId))
        if get_url: return url
        return api_call(url)

    @staticmethod
    def by_name(regionId, summonerName, get_url=False):
        """ Get a summoner SummonerDTO by summoner name.
        :param regionId: LOL server ID. Accepted values: 0-11(inclusive) for 'BR1', 'EUN1', 'EUW1', 'JP1', 'KR', 'LA1', 'LA2', 'NA1', 'OC1', 'RU' & 'TR1'
        :param summonerName: Name as shown in the League Client (can contain not-alphabetic chars)
        :param get_url: When true, don't make an API call and returns the url connection
        :return: JSON object retrieved from riot API call (or link when get_url is True)
        """
        url_base = to_url_base(regions[regionId], '/lol/summoner/v4/summoners/by-name/{summonerName}')
        url = url_base.replace('{summonerName}', attribute_formatter(summonerName))
        if get_url: return url
        return api_call(url)

    @staticmethod
    def by_puuid(regionId, encryptedPUUID, get_url=False):
        """ Get a summoner SummonerDTO by PUUID
        :param regionId: LOL server ID. Accepted values: 0-11(inclusive) for 'BR1', 'EUN1', 'EUW1', 'JP1', 'KR', 'LA1', 'LA2', 'NA1', 'OC1', 'RU' & 'TR1'
        :param encryptedPUUID: Public User ID's are globally unique. Different APIs use different IDs
        :param get_url: When true, don't make an API call and returns the url connection
        :return: JSON object retrieved from riot API call (or link when get_url is True)
        """
        url_base = to_url_base(regions[regionId], '/lol/summoner/v4/summoners/by-puuid/{encryptedPUUID}')
        url = url_base.replace('{encryptedPUUID}', attribute_formatter(encryptedPUUID))
        if get_url: return url
        return api_call(url)

    @staticmethod
    def by_encrypted_summoner_id(regionId, encryptedSummonerId, get_url=False):
        """ Get a summoner SummonerDTO by summoner ID
        :param regionId: LOL server ID. Accepted values: 0-11(inclusive) for 'BR1', 'EUN1', 'EUW1', 'JP1', 'KR', 'LA1', 'LA2', 'NA1', 'OC1', 'RU' & 'TR1'
        :param encryptedSummonerId: Summoner IDs are only unique per region. Different APIs use different IDs
        :param get_url: When true, don't make an API call and returns the url connection
        :return: JSON object retrieved from riot API call (or link when get_url is True)
        """
        url_base = to_url_base(regions[regionId], '/lol/summoner/v4/summoners/{encryptedSummonerId}')
        url = url_base.replace('{encryptedSummonerId}', attribute_formatter(encryptedSummonerId))
        if get_url: return url
        return api_call(url)

# uses ddragon static information
class Version:
    """ Allow access to version information available on DataDragon
    official DataDragon version JSON: https://ddragon.leagueoflegends.com/api/versions.json
    """
    @staticmethod
    def versions(get_url=False):
        """ Get a JSON list with all version strings
        :param get_url: When true, don't make an API call and returns the url connection
        :return: JSON object retrieved from riot API call (or link when get_url is True)
        """
        url = 'https://ddragon.leagueoflegends.com/api/versions.json'
        if get_url: return url
        return api_call(url, rate_limiting=False)

    @staticmethod
    def last_version(get_url=False):
        """ Get a string of the last version
        :param get_url: When true, don't make an API call and returns the url connection
        :return: JSON object retrieved from riot API call (or link when get_url is True)
        """
        url = 'https://ddragon.leagueoflegends.com/api/versions.json'
        if get_url: return url
        return api_call(url, rate_limiting=False)[0]