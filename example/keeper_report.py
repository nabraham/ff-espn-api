from datetime import datetime
from pathlib import Path
from ff_espn_api import League
from collections import namedtuple
import argparse
import json
import os

Keeper = namedtuple('Keeper', ['eligible', 'price', 'doubled'])


def pretty_keepers(keeper_data, team_dict, player_dict) -> None:
    pretty = []
    for player_id, (keep, price, doubled) in keeper_data:
        team_name = team_dict[player_id].team_name
        player_name = player_dict[player_id]
        icon = ['', '(x2)'][doubled]
        pretty.append('%s - $%d %s %s' % (team_name, price, player_name, icon))
    print('\n'.join(pretty))


def is_eligible(player_id, draft, prev_draft, acq_dict) -> Keeper:
    not_in_draft = player_id not in draft
    add_acquisition = acq_dict[player_id] == 'ADD'
    gt_30 = player_id in draft and draft.get(player_id).bid_amount >= 30
    keeper_gt_20 = player_id in draft and draft.get(player_id).keeper_status and draft.get(player_id).bid_amount >= 20
    kept_twice = player_id in draft and draft.get(player_id).keeper_status and \
                 player_id in prev_draft and prev_draft.get(player_id).keeper_status

    if not_in_draft or add_acquisition or gt_30 or keeper_gt_20 or kept_twice:
        return Keeper(False, 0, False)
    elif draft.get(player_id).keeper_status:
        return Keeper(True, draft.get(player_id).bid_amount * 2, True)
    else:
        return Keeper(True, draft.get(player_id).bid_amount, False)


def build_draft_dict(draft):
    return dict(list(map(lambda x: (x.playerId, x), draft)))


def main(league_id, league_year, s2, swid):
    curr = League(league_id, league_year, s2, swid)
    curr_draft = build_draft_dict(curr.draft)
    team_dict = dict([(p.playerId, t) for t in curr.teams for p in t.roster])
    acq_dict = dict([(p.playerId, p.acquisitionType) for t in curr.teams for p in t.roster])
    roster_players = [p for p in team_dict]

    prev = League(league_id, year - 1, s2, swid)
    prev_draft = build_draft_dict(prev.draft)

    player_keepers = map(lambda x: (x, is_eligible(x, curr_draft, prev_draft, acq_dict)), roster_players)
    keeper_choices = list(filter(lambda x: x[1].eligible, player_keepers))
    pretty_keepers(keeper_choices, team_dict, curr.player_map)


if __name__ == '__main__':
    year = datetime.today().year - 1
    parser = argparse.ArgumentParser(description='Keeper Report Generator')
    parser.add_argument('--year', type=int, default=year, help='The year to generate (default is current - 1 [%d])' % year)
    with open(os.path.sep.join([str(Path.home()), '.config', 'ff-espn-api', 'config.json'])) as f:
        data = json.load(f)
        parser.add_argument('--league_id', type=int, default=int(data['league_id']), help='The espn league id.  Default is specified in $HOME/.config/ff-espn-api/config.json')
        parser.add_argument('--s2', type=str, default=data['s2'], help='The espn s2 token.  Default is specified in $HOME/.config/ff-espn-api/config.json')
        parser.add_argument('--swid', type=str, default=data['swid'], help='The espn swid.  Default is specified in $HOME/.config/ff-espn-api/config.json')
        args = parser.parse_args()
        main(args.league_id, args.year, args.s2, args.swid)
