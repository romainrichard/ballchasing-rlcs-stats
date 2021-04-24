"""
Get stats from pro matches to compare the average speed of players.
"""
import os.path
from collections import defaultdict
from configparser import ConfigParser
from csv import DictWriter
from typing import Dict, List

from ballchasing import Api

CONFIG_FILE = "config.ini"


# Those groups are based on what is available on ballchasing.com:
# * https://ballchasing.com/group/rlcs-x-whqc4pi1kw for RLCS X
# * https://ballchasing.com/group/apl-nationals-p29o5i2xrb for APL Nationals
# Can't get the data per region directly because there are too many replays
# and ballchasing.com doesn't send back the stats we need.
RLCS_GROUPS = {
    "Europe": ["split-1-nak68e78tp", "split-2-b3qwqoey3n", "split-3-onrop1o3xw"],
    "North America": ["split-1-8nncsg8300", "split-2-p7l5r6a4g3", "split-3-ehllp9zru7"],
    "Oceania": ["split-1-o6t6ng61v5", "split-2-rlol6e1y5i"],
    "South America": ["split-1-t6wdw60ecf", "split-2-ldbuw0cdkw"],
    "India": ["india-eminku57a9"],
    "Indonesia": ["indonesia-8dbfqc21wl"],
    "Japan": ["japan-aiz9rm6f5u"],
    "Saudi Arabia": ["saudi-arabia-xtdxursxc8"],
    "Singapore": ["singapore-l09c6n1hj4"],
}


def get_stats(api: Api):
    """
    Get the average speed of the players and compile that stat based on:
    * The player
    * The player's team
    * The player's region
    """
    regions = defaultdict(list)
    teams = defaultdict(lambda: defaultdict(list))
    players = defaultdict(lambda: defaultdict(list))

    # Get the average speed of all the players
    for region in RLCS_GROUPS:
        for group_id in RLCS_GROUPS[region]:
            group_stats = api.get_group(group_id)
            for player in group_stats["players"]:
                avg_speed = player["game_average"]["movement"]["avg_speed"]
                regions[region].append(avg_speed)
                teams[region][player["team"]].append(avg_speed)
                players[region][player["name"]].append(avg_speed)

    # Compute the average speed overall
    for region, avg_speed in regions.items():
        regions[region] = int(sum(avg_speed) / len(avg_speed))
    for region in teams:
        for team, avg_speed in teams[region].items():
            teams[region][team] = int(sum(avg_speed) / len(avg_speed))
    for region in players:
        for player, avg_speed in players[region].items():
            players[region][player] = int(sum(avg_speed) / len(avg_speed))

    return {
        "regions": regions,
        "teams": teams,
        "players": players,
    }


def export_stats(stats: Dict):
    """
    Export the stats to CSV files.
    """
    # Regions stats
    regions = stats["regions"]
    filename = "regions.csv"
    fieldnames = ["Region", "Average speed"]
    data = [
        {"Region": region, "Average speed": avg_speed}
        for region, avg_speed in regions.items()
    ]
    export_to_csv(filename, data, fieldnames)

    # Teams stats
    teams = stats["teams"]
    filename = "teams.csv"
    fieldnames = ["Team", "Region", "Average speed"]
    data = [
        {"Team": team, "Region": region, "Average speed": avg_speed}
        for region in teams
        for team, avg_speed in teams[region].items()
    ]
    export_to_csv(filename, data, fieldnames)

    for region in teams:
        filename = f"teams-{region}.csv"
        fieldnames = ["Team", "Average speed"]
        data = [
            {"Team": team, "Average speed": avg_speed}
            for team, avg_speed in teams[region].items()
        ]
        export_to_csv(filename, data, fieldnames)

    # Players stats
    players = stats["players"]
    filename = "players.csv"
    fieldnames = ["Player", "Region", "Average speed"]
    data = [
        {"Player": player, "Region": region, "Average speed": avg_speed}
        for region in players
        for player, avg_speed in players[region].items()
    ]
    export_to_csv(filename, data, fieldnames)

    for region in players:
        filename = f"players-{region}.csv"
        fieldnames = ["Player", "Average speed"]
        data = [
            {"Player": player, "Average speed": avg_speed}
            for player, avg_speed in players[region].items()
        ]
        export_to_csv(filename, data, fieldnames)


def export_to_csv(output_csv: str, data: List, fieldnames: List):
    """
    Export the data to a CSV file for sharing.
    """
    # Sort the data by speed
    data = sorted(data, key=lambda stat: stat["Average speed"], reverse=True)
    with open(os.path.join("csv", output_csv), "w", newline="") as f:
        writer = DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


def get_api():
    """
    Initialize the ballchasing API object.
    """
    config = ConfigParser()
    config.read(CONFIG_FILE)
    return Api(config["DEFAULT"]["API_KEY"])


def main():
    api = get_api()
    stats = get_stats(api)
    export_stats(stats)


if __name__ == "__main__":
    main()
