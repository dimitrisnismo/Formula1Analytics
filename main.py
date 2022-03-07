import pandas as pd
import numpy as np
import fastf1
import seaborn as sns
import matplotlib.pyplot as plt
import streamlit as st

sns.set()

fastf1.Cache.enable_cache(r"C:\Cachef1")  # replace with your cache directory

st.set_page_config(
    page_title="Formula 1 Data Analysis",
    page_icon="Images\\f1logo.png",
    layout="centered",
    initial_sidebar_state="auto",
    menu_items=None,
)
st.title("Formula 1 Tyre Analysis")
i = 1

# array(['Alpine F1 Team', 'Mercedes', 'AlphaTauri', 'Alfa Romeo',
#        'Williams', 'Ferrari', 'Haas F1 Team', 'McLaren', 'Red Bull',
#        'Aston Martin'], dtype=object)
# List of Drivers ['VER', 'HAM', 'BOT', 'LEC', 'GAS', 'RIC', 'NOR', 'SAI', 'ALO',
#        'STR', 'PER', 'GIO', 'TSU', 'RAI', 'RUS', 'OCO', 'LAT', 'MSC',
#        'MAZ', 'VET']
# Running for each session


@st.cache()
def load_race_data():
    df = pd.DataFrame()
    count = 1
    while count <= 22:
        race = fastf1.get_session(2021, count, "R")
        laps = race.load_laps(with_telemetry=True)
        laps["Race"] = race.weekend.name
        df = pd.concat([df, laps])
        count += 1
    return df


data = load_race_data()

df = pd.DataFrame()


def remove_wet_races(data):
    wet_races = (
        data[["Race", "Compound", "LapTime"]]
        .groupby(["Race", "Compound"])
        .count()
        .reset_index()
    )
    wet_races = pd.pivot_table(
        wet_races, index="Race", columns="Compound", values="LapTime"
    ).reset_index()
    wet_races = wet_races.fillna(0)
    wet_races = wet_races[(wet_races["WET"] == 0) & (wet_races["INTERMEDIATE"] == 0)]
    data = pd.merge(data, wet_races[["Race"]], on="Race")
    return data


def add_difference_from_the_car_in_front(data):
    # Sort Values by Following Car
    data = data.sort_values(by=["Race", "Time"]).reset_index(drop=True)
    ##Add column with the delta between 2 cars in the beginning of the lap
    data["followingcar"] = data["Time"] - data["Time"].shift(1)
    return data


def filter_dataframe(data):
    # Filter Dataframe where
    # 1.there is no pit in or pit out in this lap
    # 2.The track is Clear
    # 3.there is no car ahead less than 1 second
    # 4.Only Dry Tyres
    # 5.Keeping only necessery Columns
    data = data[
        (data["PitOutTime"].isnull())
        & (data["PitInTime"].isnull())
        & (data["TrackStatus"] == "1")
        & (data["followingcar"] > pd.Timedelta(1.1, unit="s"))
    ][
        [
            "LapTime",
            "LapNumber",
            "Compound",
            "TyreLife",
            "Team",
            "Driver",
        ]
    ]
    return data


# Creating a column with the tyre delta between the laps
laps = laps.sort_values(by=["Driver", "LapNumber", "TyreLife", "Compound"]).reset_index(
    drop=True
)
laps["tyredelta"] = np.where(
    (laps["Driver"] == laps["Driver"].shift(1))
    & (laps["Compound"] == laps["Compound"].shift(1)),
    pd.to_timedelta(laps["LapTime"] - laps["LapTime"].shift(1)),
    pd.NaT,
)
laps["tyredelta"] = laps["tyredelta"].fillna(9999 * 1000)
laps["tyredelta"] = (laps["tyredelta"] / 1000).astype("int")

# Drop rows where there are containing na values
laps = laps.dropna()

# Calculating Lap Times in Seconds
laps["lapinseconds"] = laps["LapTime"] / np.timedelta64(1, "s")

# The Tyre Compounds
Compounds = ["SOFT", "MEDIUM", "HARD"]

##Clean lap Time per Compound
# For each compound using Quartile Analysis removing Outliers
# Using Rolling 5 lap Times in order to normalize data and to be easier to analyze
dftemp = pd.DataFrame()
for compound in Compounds:
    df_compound = laps[laps["Compound"] == compound]
    Q1 = df_compound["lapinseconds"].quantile(0.25)
    Q3 = df_compound["lapinseconds"].quantile(0.75)
    IQR = Q3 - Q1
    df_compound = df_compound[
        ~(
            (df_compound["lapinseconds"] < (Q1 - 1.5 * IQR))
            | (df_compound["lapinseconds"] > (Q3 + 1.5 * IQR))
        )
    ]
    df_compound = (
        df_compound[["lapinseconds", "TyreLife"]]
        .groupby(["TyreLife"])
        .mean()
        .reset_index(drop=False)
    )
    df_compound["RollingLapTime"] = (
        df_compound["lapinseconds"]
        .rolling(window=5, min_periods=1)
        .mean()
        .fillna(df_compound["lapinseconds"])
    )
    df_compound["Compound"] = compound
    df_compound["Race"] = race.weekend.name
    dftemp = pd.concat([dftemp, df_compound])
    df = pd.concat([df, df_compound])

##Visualizing Results
pd.pivot_table(
    dftemp, values="RollingLapTime", columns="Compound", index="TyreLife"
).plot(title=race.weekend.name)
i = i + 1
# asdasf