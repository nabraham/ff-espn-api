from datetime import datetime
from pathlib import Path
from ff_espn_api import League
import json
import os
import sys


def pretty_keepers(keeper_data, team_dict, player_dict):
    pretty = []
    for player_id, (keep, price, doubled) in keeper_data:
        team_name = team_dict[player_id].team_name
        player_name = player_dict[player_id]
        icon = ['', '(x2)'][doubled]
        pretty.append('%s - $%d %s %s' % (team_name, price, player_name, icon))
    print('\n'.join(pretty))


def is_eligible(player_id, draft, prev_draft, acq_dict, player_dict):

    if player_id not in draft:
        return False, 0, False
    elif acq_dict[player_id] == 'ADD':
        p = player_dict.get(player_id, 'not found')
        return False, 0, False
    elif draft.get(player_id).bid_amount >= 30:
        return False, 0, False
    elif draft.get(player_id).keeper_status:
        if draft.get(player_id).bid_amount >= 20:
            return False, 0, False
        elif player_id in prev_draft and prev_draft.get(player_id).keeper_status:
            return False, 0, False
        else:
            return True, draft.get(player_id).bid_amount * 2, True
    else:
        return True, draft.get(player_id).bid_amount, False


def build_draft_dict(draft):
    return dict(list(map(lambda x: (x.playerId, x), draft)))


def main(league_id, league_year, s2, swid):
    curr = League(league_id, league_year, s2, swid)
    curr_draft = build_draft_dict(curr.draft)
    team_dict = dict([(p.playerId, t) for t in curr.teams for p in t.roster])
    acq_dict = dict([(p.playerId, p.acquisitionType) for t in curr.teams for p in t.roster])
    roster_players = [p for p in team_dict]

    prev = League(league_id, year-1, s2, swid)
    prev_draft = build_draft_dict(prev.draft)

    eligible = map(lambda x: (x, is_eligible(x, curr_draft, prev_draft, acq_dict, curr.player_map)), roster_players)
    keeper_choices = list(filter(lambda x: x[1][0], eligible))
    pretty_keepers(keeper_choices, team_dict, curr.player_map)


if __name__ == '__main__':
    year = datetime.today().year
    if len(sys.argv) > 1:
        year = int(sys.argv[1])
    with open(os.path.sep.join([str(Path.home()), '.config', 'ff-espn-api', 'config.json'])) as f:
        data = json.load(f)
        main(data['league_id'], year, data['s2'], data['swid'])
