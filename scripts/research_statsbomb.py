from typing import Any

import pandas as pd
from statsbombpy import sb

pd.set_option('display.max_columns', None)

pd.set_option('display.max_rows', 10)


def research_statsbomb():
    print("--- 1. Competitions ---")
    try:
        competitions: Any = sb.competitions()
        print("Competitions Columns:", competitions.columns.tolist())

        print("Sample Competition:\n", competitions.head(1))

        # Pick a competition for further steps (e.g., 2018 World Cup if available,
        # otherwise just the first one)
        # Using a logic to find a likely available competition
        selected_comp = competitions.iloc[0]
        comp_id = selected_comp['competition_id']
        season_id = selected_comp['season_id']
        print(
            f"\nSelected Competition ID: {comp_id}, Season ID: {season_id}, "
            f"Name: {selected_comp['competition_name']}"
        )

    except Exception as e:
        print(f"Error fetching competitions: {e}")
        return

    print("\n--- 2. Matches ---")
    try:
        matches: Any = sb.matches(competition_id=comp_id, season_id=season_id)
        print("Matches Columns:", matches.columns.tolist())

        print("Sample Match:\n", matches.head(1))

        if matches.empty:
            print("No matches found for this competition.")
            return

        selected_match_id = matches.iloc[0]['match_id']
        print(f"\nSelected Match ID: {selected_match_id}")

    except Exception as e:
        print(f"Error fetching matches: {e}")
        return

    print("\n--- 3. Events ---")
    try:
        events: Any = sb.events(match_id=selected_match_id)
        print("Events Columns:", events.columns.tolist())

        # Check specific fields of interest
        interesting_columns = [
            'player_id', 'player', 'team_id', 'team', 'position',
            'type', 'location', 'timestamp', 'minute', 'second'
        ]

        available_interesting = [
            col for col in interesting_columns if col in events.columns]
        print("\nRequested Key Fields Availability:")
        for col in interesting_columns:
            print(f"  {col}: {'Present' if col in events.columns else 'Missing'}")

        print("\nSample Event (first 5 columns):\n",
              events.iloc[0][available_interesting[:5]])

        # Check for coordinates in location
        if 'location' in events.columns:
            # location is usually a list/series of [x, y]
            sample_loc = events['location'].dropna().iloc[0]
            print(
                f"\nSample Location format: {sample_loc} (Type: {type(sample_loc)})")

    except Exception as e:
        print(f"Error fetching events: {e}")


if __name__ == "__main__":
    research_statsbomb()
