import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.dates as md
from matplotlib import rcParams

# content-invariant style
rcParams['figure.dpi'] = 300

# load
df = pd.read_csv("data.csv", index_col="client_time_iso")

# drop things we don't need (big dataframes...)
df = df.drop(columns=["roundtrip_delay"])

# typing...grrr
df.index = pd.to_datetime(df.index, format="ISO8601")


#print(hue_order)

days_df = [day_group for day_group in df.groupby(df.index.date)]
days_df = days_df[:2]

for day_df in days_df:
    date = day_df[0].strftime('%Y-%m-%d')
    day_df = day_df[1]

    day_df.reset_index(inplace=True)
    # Extract time component from the timestamp
    #day_df['time'] = day_df['client_time_iso'].dt.time

    #print(f"Processing data for date: {date}")

    print(day_df.index.dtype)
    #day_df.index = pd.to_datetime(day_df.index)
    print(day_df.index.dtype)

    day_df["client_time_iso"] = pd.to_datetime(day_df["client_time_iso"], format="ISO8601")
    day_df['hour'] = day_df["client_time_iso"].dt.hour

    hours = day_df['hour'].unique()
    nrows = len(hours)

    # figure size in inches
    rcParams['figure.figsize'] = 50, nrows*4

    fig, axs = plt.subplots(
        ncols=1,
        nrows=nrows,
        )

    # Same order in all figures
    actions = df["action"].unique()
    hue_order = sorted(actions)


    for ix, hour in enumerate(hours):
        print(hour)
        hour_df = day_df.loc[day_df['hour'] == hour]
        axi = axs[ix]

        sns.lineplot(
            data=hour_df,
            x="client_time_iso",
            y="state",
            hue="action",
            palette="tab10",
            linewidth=.5,
            ax=axi,
            hue_order=hue_order,
        )

        axi.set_xlim(
            hour_df["client_time_iso"].min(),
            hour_df["client_time_iso"].max(),
            )
        #axi.xaxis.set_major_formatter(md.DateFormatter('%H:%M:%S.%f'))
        # Don't print femtoseconds
        axi.xaxis.set_major_formatter(md.DateFormatter('%H:%M:%S'))

    plt.title(date)

    # Remove large padding:
    plt.savefig(date+".png",
        pad_inches=.05,
        bbox_inches='tight'
        )
    plt.close()
