import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.dates as md

from matplotlib import rcParams
from matplotlib.collections import EventCollection

# content-invariant style
rcParams['figure.dpi'] = 400
#rcParams['figure.dpi'] = 100

# load
base_df = pd.read_csv("DATA.csv", index_col="client_time_iso")

# drop things we don't need (big dataframes...)
base_df = base_df.drop(columns=["roundtrip_delay"])

# typing...grrr
base_df.index = pd.to_datetime(base_df.index, format="ISO8601")


#print(hue_order)

days_df = [day_group for day_group in base_df.groupby(base_df.index.date)]
days_df = days_df[:1]

for day_df in days_df:
    date = day_df[0].strftime('%Y-%m-%d')
    print(f"Processing data for day {date}.")
    day_df = day_df[1]

    day_df.reset_index(inplace=True)
    # Extract time component from the timestamp
    #day_df['time'] = day_df['client_time_iso'].dt.time

    #print(day_df.index.dtype)
    #day_df.index = pd.to_datetime(day_df.index)
    #print(day_df.index.dtype)

    day_df["client_time_iso"] = pd.to_datetime(day_df["client_time_iso"], format="ISO8601")
    day_df['hour'] = day_df["client_time_iso"].dt.hour

    # We need this to be list type..
    hours = list(day_df['hour'].unique())
    # Remove trivial length hours
    for i in hours:
        if len(day_df.loc[day_df['hour'] == i]) <= 1:
            hours.remove(i)

    nrows = len(hours)

    # figure size in inches
    rcParams['figure.figsize'] = 50, nrows*4

    fig, axs = plt.subplots(
        ncols=1,
        nrows=nrows,
        )

    repeats_detected = False

    for ix, hour in enumerate(hours):
        print(f"\tProcessing data for hour {hour}, ix={ix}.")

        # Make actual copy so we can set new values.
        _hour_df = day_df.loc[day_df['hour'] == hour]

        #print(_hour_df)
        hour_df = _hour_df.copy()
        #print(hour_df)
        #print("=========")
        #print(hour_df)
        #print("---------")

        # Same order in all figures
        actions = hour_df["action"].unique()
        hue_order = sorted(actions)

        # Highlight repeats
        hour_df["repetition"] = np.nan
        hour_df["old_index"] = hour_df.index

        for action in actions:
            hour_action_df = hour_df.loc[hour_df['action'] == action]
            hour_action_df = hour_action_df.reset_index()
            for i in range(1, len(hour_action_df)):
                if hour_action_df.loc[i, 'state'] == hour_action_df.loc[i-1, 'state']:
                    this_entry_in_hour_df = hour_action_df.loc[i, "old_index"]
                    hour_df.loc[this_entry_in_hour_df, 'repetition'] = 1

        #if repeats_dected:
        #    print("\t\tRepeats detected:")
        #print(hour_df.loc[hour_df["repetition"] == 1]),

        axi = axs[ix]

        axi = sns.lineplot(
            data=hour_df,
            x="client_time_iso",
            y="state",
            hue="action",
            palette="tab10",
            linewidth=.2,
            ax=axi,
            hue_order=hue_order,
        )

        # Plot repetitions

        # This doesn't work with timeseries types :(
        #repeat_events = EventCollection(
        #    hour_action_df.loc[hour_action_df["repetition"] == 1]["client_time_iso"],
        #    color='tab:red',
        #    linelength=0.5,
        #    orientation='vertical',
        #    )

        axi.vlines(
            hour_df.loc[hour_df["repetition"] == 1]["client_time_iso"],
            ymin=0,
            ymax=1,
            #hour_action_df.loc[hour_action_df["repetition"] == 1],
            color='tab:red',
            linewidth=1,
            alpha=0.5,
            )
        #axi.plot(
        #    hour_action_df["client_time_iso"],
        #    hour_action_df["repetition"],
        #    #hour_action_df.loc[hour_action_df["repetition"] == 1],
        #    color='tab:red',
        #    )
        #print(hour_action_df.loc[hour_action_df["repetition"] == 1])
        #axi = sns.lineplot(
        #    data=hour_action_df,
        #    x="client_time_iso",
        #    y="repetition",
        #    linewidth=.8,
        #    ax=axi,
        #)

        # If you want custom axis padding, no lin definition gives some standard-ish padding.
        #axi.set_xlim(
        #    hour_df["client_time_iso"].min()-pd.Timedelta(minutes=10),
        #    hour_df["client_time_iso"].max()+pd.Timedelta(minutes=10),
        #    )
        axi.set_xlim(
            hour_df["client_time_iso"].min(),
            hour_df["client_time_iso"].max(),
            )
        # This won't display correct hours for some reason
        #axi.xaxis.set_major_formatter(md.DateFormatter('%d-%H:%M:%S.%f'))
        # Don't print femtoseconds
        #axi.xaxis.set_major_formatter(md.DateFormatter('%H:%M:%S'))

        axi.set(title=f"{date} hour {hour}, value-repeat events in red.")
        axi.set(xlabel=None)


    # y-Position is hard to wonky
    #plt.suptitle(f"{date}", y=0.9)
    # Remove large padding:
    plt.savefig(date+".png",
        pad_inches=.1,
        bbox_inches='tight'
        )
    plt.close()
    print(f"\t ✔️ Done.")
