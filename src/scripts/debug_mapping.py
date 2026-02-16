import pandas as pd

from src.analytics.doppelganger.config import POSITION_MAPPINGS
from src.analytics.doppelganger.etl import assign_position_group


def test_mapping():
    print("MAPPINGS:", POSITION_MAPPINGS)

    df = pd.DataFrame(
        [{"id": 10955, "name": "Harry Kane", "position": "Center Forward"}]
    )

    result = assign_position_group(df)
    print("\nResult for Center Forward:")
    print(result)

    mapped_val = result.iloc[0]
    print(f"\nMapped Value: '{mapped_val}'")

    if mapped_val == "FWD":
        print("SUCCESS: Mapping works correctly in isolation.")
    else:
        print("FAILURE: Mapping failed.")


if __name__ == "__main__":
    test_mapping()
