from statsbombpy import sb
import pandas as pd


def preview_statsbomb_data():
    print("--- Fetching Competitions ---")
    competitions = sb.competitions()
    print(competitions.head())

    # Let's find the 2022 World Cup (Competition ID 43, Season ID 106)
    # usually available in open data
    print("\n--- Fetching Matches for World Cup 2022 ---")
    try:
        matches = sb.matches(competition_id=43, season_id=106)
        print(matches.head())

        if not matches.empty:
            first_match_id = matches.iloc[0]['match_id']
            print(f"\n--- Fetching Events for Match {first_match_id} ---")
            events = sb.events(match_id=first_match_id)
            print(events[['type', 'player', 'team',
                  'location', 'timestamp']].head(10))
            print("\n--- Available Columns ---")
            print(list(events.columns))
    except Exception as e:
        print(f"Could not fetch specific competition: {e}")


if __name__ == "__main__":
    preview_statsbomb_data()
