import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import sys

# Configurable Bill
MONTHLY_BILL = 580
SPEED_THRESHOLD = 25 * 1e6  # 25 Mbps in bps
LOW_SPEED_THRESHOLD = 10 * 1e6

if  len(sys.argv) <= 1:
    print("Pass csv file as argument")
    sys.exit(1)
else:
    CSV_FILE_PATH = sys.argv[1]


def process_speedtest(csv_file):
    df = pd.read_csv(csv_file, parse_dates=["Created at"])

    # Data Cleaning
    df["Download"] = pd.to_numeric(df["Download"], errors="coerce")
    df["Upload"] = pd.to_numeric(df["Upload"], errors="coerce")
    df["Download_Mbps"] = df["Download"].div(1e6).fillna(0)
    df["Upload_Mbps"] = df["Upload"].div(1e6).fillna(0)
    df["Status"] = df["Status"].fillna("Unknown")

    # Scatter Plot
    color_conditions = [
        (df["Status"] == "Failed") | (df["Download_Mbps"] < 10),
        (df["Download_Mbps"] >= 10) & (df["Download_Mbps"] < 25),
        df["Download_Mbps"] >= 25,
    ]
    colors = ["red", "yellow", "green"]
    df["color"] = np.select(color_conditions, colors, default="red")

    plt.figure(figsize=(15, 5))
    plt.scatter(df["Created at"], df["Download_Mbps"], c=df["color"])
    plt.xlabel("Time")
    plt.ylabel("Download Speed (Mbps)")
    plt.title("Download Speed Scatter Plot")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("download_speed_scatter.png")
    plt.close()

    # Hourly Aggregation
    df["hour_slot"] = df["Created at"].dt.floor("h")
    hourly = (
        df.groupby("hour_slot")
        .agg(
            min_download=("Download", lambda x: x.min() if x.any() else 0),
            min_upload=("Upload", lambda x: x.min() if x.any() else 0),
            has_fail=("Status", lambda x: (x == "Failed").any()),
            avg_download_mbps=("Download_Mbps", "mean"),
        )
        .reset_index()
    )

    hourly["unstable"] = (
        hourly["has_fail"]
        | (hourly["min_download"] < SPEED_THRESHOLD)
        | (hourly["min_upload"] < SPEED_THRESHOLD)
    )

    total_slots = len(hourly)
    unstable_slots = hourly["unstable"].sum()
    rebate = (unstable_slots / total_slots) * MONTHLY_BILL

    # Bar Plot
    bar_colors = np.where(
        hourly["avg_download_mbps"] < 10,
        "red",
        np.where(hourly["avg_download_mbps"] < 25, "yellow", "green"),
    )

    plt.figure(figsize=(15, 5))
    plt.bar(hourly["hour_slot"], hourly["avg_download_mbps"], color=bar_colors)
    plt.xlabel("Hourly Slot")
    plt.ylabel("Avg Download Speed (Mbps)")
    plt.title("Hourly Internet Stability")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("hourly_internet_stability.png")
    plt.close()

    # Heatmap: Convert to int BEFORE pivot
    heatmap_df = hourly.copy()
    heatmap_df["unstable"] = heatmap_df["unstable"].astype(int)  # Convert to int here
    heatmap_df["date"] = heatmap_df["hour_slot"].dt.date
    heatmap_df["hour"] = heatmap_df["hour_slot"].dt.hour
    heatmap_pivot = heatmap_df.pivot(index="hour", columns="date", values="unstable")

    plt.figure(figsize=(12, 7))
    sns.heatmap(
        heatmap_pivot,
        cmap=["green", "red"],
        cbar=False,
        linewidths=0.5,
        linecolor="gray",
    )
    plt.title("Internet Stability Heatmap (Green = Stable, Red = Unstable)")
    plt.ylabel("Hour of Day")
    plt.xlabel("Date")
    plt.tight_layout()
    plt.savefig("internet_stability_heatmap.png")
    plt.close()

    # Rebate Output
    print(f"Total Slots: {total_slots}")
    print(f"Unstable Slots: {unstable_slots}")
    print(f"Rebate Amount: ₹{rebate:.2f}")
    print(f"Final Payable Amount: ₹{MONTHLY_BILL - rebate:.2f}")


if __name__ == "__main__":
    process_speedtest(CSV_FILE_PATH)
