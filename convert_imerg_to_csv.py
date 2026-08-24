import os
import xarray as xr
import pandas as pd

# ============================================================
# SETTINGS
# ============================================================

INPUT_DIR = "imerg_2024"
OUTPUT_DIR = "imerg_csv"

# Chennai coordinates
CHENNAI_LAT = 13.08
CHENNAI_LON = 80.27

# Create output directory
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================
# FIND NETCDF FILES
# ============================================================

files = [
    f for f in os.listdir(INPUT_DIR)
    if f.lower().endswith(".nc4")
]

files.sort()

print(f"Found {len(files)} NetCDF files.")

if len(files) == 0:
    print("No .nc4 files found.")
    exit()


# ============================================================
# STORE ALL RESULTS
# ============================================================

all_data = []


# ============================================================
# PROCESS EVERY FILE
# ============================================================

for i, filename in enumerate(files, start=1):

    file_path = os.path.join(INPUT_DIR, filename)

    print()
    print("============================================")
    print(f"Processing {i}/{len(files)}")
    print(filename)
    print("============================================")

    try:

        # ----------------------------------------------------
        # OPEN NETCDF
        # ----------------------------------------------------

        ds = xr.open_dataset(file_path)

        # ----------------------------------------------------
        # CHECK VARIABLES
        # ----------------------------------------------------

        if "precipitation" not in ds:

            print("ERROR: precipitation variable not found.")

            print("Available variables:")
            print(list(ds.data_vars))

            ds.close()
            continue

        # ----------------------------------------------------
        # FIND CHENNAI GRID CELL
        # ----------------------------------------------------

        chennai = ds["precipitation"].sel(
            lat=CHENNAI_LAT,
            lon=CHENNAI_LON,
            method="nearest"
        )

        # ----------------------------------------------------
        # EXTRACT RAINFALL
        # ----------------------------------------------------

        rainfall = float(chennai.values.squeeze())

        # ----------------------------------------------------
        # EXTRACT ACTUAL GRID COORDINATES
        # ----------------------------------------------------

        latitude = float(
            chennai.lat.values
        )

        longitude = float(
            chennai.lon.values
        )

        # ----------------------------------------------------
        # EXTRACT DATE
        # ----------------------------------------------------

        date = pd.to_datetime(
            chennai.time.values[0]
        )

        # ----------------------------------------------------
        # PRINT RESULT
        # ----------------------------------------------------

        print("Nearest grid latitude :", latitude)
        print("Nearest grid longitude:", longitude)
        print("Date                  :", date)
        print("Chennai rainfall      :", rainfall, "mm")

        # ----------------------------------------------------
        # CREATE DATAFRAME
        # ----------------------------------------------------

        df = pd.DataFrame({
            "date": [date],
            "latitude": [latitude],
            "longitude": [longitude],
            "rainfall_mm": [rainfall]
        })

        # ----------------------------------------------------
        # CREATE INDIVIDUAL CSV
        # ----------------------------------------------------

        csv_filename = os.path.splitext(filename)[0] + ".csv"

        csv_path = os.path.join(
            OUTPUT_DIR,
            csv_filename
        )

        df.to_csv(
            csv_path,
            index=False
        )

        print("Saved:", csv_path)

        # ----------------------------------------------------
        # ADD TO COMBINED DATA
        # ----------------------------------------------------

        all_data.append(df)

        ds.close()

    except Exception as e:

        print("ERROR:", e)


# ============================================================
# CREATE COMBINED CSV
# ============================================================

if all_data:

    combined_df = pd.concat(
        all_data,
        ignore_index=True
    )

    # Sort by date
    combined_df = combined_df.sort_values(
        by="date"
    )

    # Reset index
    combined_df = combined_df.reset_index(
        drop=True
    )

    combined_path = os.path.join(
        OUTPUT_DIR,
        "chennai_rainfall_2024.csv"
    )

    combined_df.to_csv(
        combined_path,
        index=False
    )

    print()
    print("============================================")
    print("ALL FILES PROCESSED")
    print("============================================")

    print("Total records:", len(combined_df))

    print()
    print("Combined CSV:")
    print(combined_path)

    print()
    print(combined_df)

else:

    print()
    print("No rainfall data was extracted.")