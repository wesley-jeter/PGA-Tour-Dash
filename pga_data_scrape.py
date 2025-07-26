import requests
import pandas as pd
from functools import reduce

### this was way harder than it should have been

# defning api key, URL to send POST request, and header
API_KEY     = "da2-gsrx5bibzbb4njvhl7t37wqyl4"
GRAPHQL_URL = "https://orchestrator.pgatour.com/graphql"
HEADERS     = {
    "x-api-key":    API_KEY,
    "Content-Type": "application/json",
    "User-Agent":   "python-requests"
}

# mapping metric names to their ids
stat_ids = {
    "ScoringAvg": "120",
    "SGTotal":    "02675",
    "SGOffTee":   "02567",
    "SGApproach": "02568",
    "SGAround":   "02569",
    "SGPutting":  "02564",
    "FedEx":      "02671",
    "Money":      "109"
}

# GraphQL (never heard of it) query, big time chatgpt help here
stat_query = """
query StatDetails($tourCode:TourCode!,$statId:String!,$year:Int){
  statDetails(tourCode:$tourCode, statId:$statId, year:$year){
    rows {
      ... on StatDetailsPlayer {
        playerId
        playerName
        country
        stats { statValue }
      }
    }
  }
}
"""

dfs = []

# iterates through each stat
for name, sid in stat_ids.items():

    # json request body with GraphQL query
    payload = {
        "operationName": "StatDetails",
        "query":         stat_query,
        "variables":     {"tourCode":"R","statId":sid,"year":2025}
    }

    # send request
    resp = requests.post(GRAPHQL_URL, headers=HEADERS, json=payload)

    # error if request fails
    resp.raise_for_status()

    # converts json response to python dict and extracts the rows (each players data)
    rows = resp.json()["data"]["statDetails"]["rows"]

    # initialize df for stat
    records = []

    # iterating through each row (player) received from the request
    for r in rows:

        # handles grabbing stat correctly and dealing with missing values
        if "stats" in r and r["stats"]:
            raw = r["stats"][0].get("statValue")
        elif "statValue" in r:
            raw = r.get("statValue")
        else:
            continue

        # reads normalizes strings to floats
        clean = raw.replace(",", "")
        if name == "Money":
            clean = clean.replace("$", "")
        val = float(clean)

        # appends the row (player) to the df
        records.append({
            "playerId": r["playerId"],
            "fullName": r["playerName"],
            "country":  r["country"],
            name:       val
        })


    dfs.append(pd.DataFrame(records))

dfs_cleaned = []

# removing country and player name from each stat df to avoid merging error
for df in dfs:
    dfs_cleaned.append(df[["playerId"] + [col for col in df.columns if col not in ["fullName", "country"] and col != "playerId"]])


# mergin all the dfs on playerid
df_all = reduce(
    lambda left, right: pd.merge(
        left,
        right,
        on="playerId",
        how="outer"
    ),
    dfs_cleaned
)

name_country = []

# have to reattach the names and countries, annoyingly some players have null stats
for df in dfs:
    meta_subset = df[["playerId", "fullName", "country"]].dropna(subset=["playerId"])
    name_country.append(meta_subset)

# concats the name country dfs, drops duplicates, resets index
name_country_df = (pd.concat(name_country).drop_duplicates("playerId").reset_index(drop=True)
)

# Now merge it back in
df_all = df_all.merge(name_country_df, on="playerId", how="left")

# cleaning
df_all[["fullName", "country"]] = df_all[["fullName", "country"]].replace(r"[\u2019\u2018]", "'", regex=True)

df_all["firstName"] = df_all["fullName"].apply(lambda x: x.split()[0])
df_all["lastName"] = df_all["fullName"].apply(lambda x: x.split()[-1])

df_all = df_all.sort_values("lastName")

df_all["FedEx"] = df_all["FedEx"].fillna(0)
df_all["Money"] = df_all["Money"].fillna(0)

df_all.to_csv("pga_player_data.csv", index=False)