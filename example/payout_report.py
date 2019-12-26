from ff_espn_api import League, Matchup, Team
from typing import List, Tuple
from functools import reduce
from pprint import pprint
from collections import defaultdict
from pathlib import Path
from datetime import datetime
import json
import os
import sys


def high_score(matchups: List[Matchup]) -> List[Tuple[Team, int]]:
    all_scores = list(reduce(lambda x, y: x + y,
                             [[(m.away_team, m.away_score), (m.home_team, m.home_score)] for m in matchups]))
    highest = max(all_scores, key=lambda x: x[1])[1]
    return list(filter(lambda x: x[1] == highest, all_scores))


def made_playoff_round(matchups: List[Matchup]) -> List[Team]:
    active = filter(lambda x: x.is_playoff(), matchups)
    members = map(lambda x: [x.away_team, x.home_team], active)
    return list(reduce(lambda x, y: x + y, members))


def parse_10(league: League,
             dues=100,
             weekly_prize=10,
             scorer_prize=160,
             round1_prize=50,
             round2_prize=100,
             winner_prize=300) -> List[Tuple[str, float]]:
    money = defaultdict(int)

    # Winner
    champ = league.scoreboard(16)[0].winner
    money[champ.team_name] += winner_prize

    # Making playoff rounds 1, 2
    for (r, prize) in [(15, round1_prize), (16, round2_prize)]:
        for team in made_playoff_round(league.scoreboard(r)):
            money[team.team_name] += prize

    # Weekly High
    high_scorers = [high_score(league.scoreboard(week)) for week in range(1, 15)]
    for week in high_scorers:
        for team in week:
            money[team[0].team_name] += weekly_prize / len(week)

    # Point Leader
    money[league.top_scorer().team_name] += scorer_prize

    # Who owes
    payments = [(team.team_name, money[team.team_name] - dues) for team in league.teams]

    return sorted(payments, key=lambda x: -x[1])


def main(league_id, league_year, s2, swid, n_teams=10):
    league = League(league_id, league_year, s2, swid)

    if n_teams == 10:
        pprint(parse_10(league))
    elif n_teams == 12:
        raise Exception('12 teams not yet implemented')


if __name__ == '__main__':
    year = datetime.today().year
    if len(sys.argv) > 1:
        year = int(sys.argv[1])
    with open(os.path.sep.join([str(Path.home()), '.config', 'ff-espn-api', 'config.json'])) as f:
        data = json.load(f)
        main(data['league_id'], year, data['s2'], data['swid'])
