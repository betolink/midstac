# data access and processing
import calendar
import logging
import os
import warnings
from typing import Optional

import cartopy.crs as ccrs
import earthaccess as ea
import fsspec
import matplotlib.pyplot as plt
import requests
import xarray as xr
import zarr

# distributed compute
from dask.distributed import Client, LocalCluster

auth = ea.login()
ds = None
client = None
cluster = None

API_KEY_IMGBB = os.getenv("IMGBB_API_KEY")


def create_dask_cluster(n_workers=4, cloud_opts=None) -> tuple[Client, LocalCluster]:
    if cloud_opts is None:
        cloud_opts = {}
    global client, cluster

    if client is not None and cluster is not None:
        return (client, cluster)

    print("Creating new local Dask client")
    cluster = LocalCluster(n_workers=n_workers, threads_per_worker=1, silence_logs=logging.ERROR)
    client = Client(cluster)
    return (client, cluster)


def silence_worker_warnings():
    warnings.filterwarnings("ignore")
    for name in ["distributed", "xarray", "py.warnings", "fsspec", "h5netcdf", "h5py"]:
        logging.getLogger(name).setLevel(logging.ERROR)


def upload_image_to_imgbb(image_path: str) -> Optional[str]:
    """Upload image to imgbb.com and return the hosted URL."""
    with open(image_path, "rb") as f:
        image_bytes = f.read()
    response = requests.post(
        "https://api.imgbb.com/1/upload",
        params={"key": API_KEY_IMGBB},
        files={"image": image_bytes},
    )
    response.raise_for_status()
    return response.json()["data"]["url"]


def plot_seasonal_smap_area(
    ds, varname, lat_min, lat_max, lon_min, lon_max, month_start, month_end, year, operation="std"
) -> Optional[str]:
    WGS84 = ccrs.PlateCarree()
    EASEGrid2 = ccrs.epsg(6933)
    x_min, y_min = EASEGrid2.transform_point(lon_min, lat_min, WGS84)
    x_max, y_max = EASEGrid2.transform_point(lon_max, lat_max, WGS84)
    if y_min > y_max:
        y_min, y_max = y_max, y_min
    ds_bbox = ds[varname].sel(x=ds.x[(ds.x >= x_min) & (ds.x <= x_max)], y=ds.y[(ds.y >= y_min) & (ds.y <= y_max)])

    if len(ds_bbox.x) == 0 or len(ds_bbox.y) == 0:
        print("ERROR: No data in selected region!")
        return None

    # Filter by year
    ds_year = ds_bbox.sel(time=ds_bbox.time.dt.year == year)

    # Filter by season
    if month_end < month_start:
        mask = (ds_year.time.dt.month >= month_start) | (ds_year.time.dt.month <= month_end)
    else:
        mask = (ds_year.time.dt.month >= month_start) & (ds_year.time.dt.month <= month_end)
    ds_seasonal = ds_year.sel(time=mask)

    if len(ds_seasonal.time) == 0:
        print("No data in selected time period!")
        return None

    # Define operations that work directly on time dimension
    operations = {
        "std": lambda x: x.std(dim="time"),
        "mean": lambda x: x.mean(dim="time"),
        "median": lambda x: x.median(dim="time"),
        "min": lambda x: x.min(dim="time"),
        "max": lambda x: x.max(dim="time"),
        "sum": lambda x: x.sum(dim="time"),
        "var": lambda x: x.var(dim="time"),
    }

    if operation not in operations:
        print(f"Operation {operation} not supported. Choose from: {list(operations.keys())}")
        return None

    # Apply operation directly (no groupby needed)
    yearly_agg = operations[operation](ds_seasonal)

    operation_labels = {
        "std": "Std Dev",
        "mean": "Mean",
        "median": "Median",
        "min": "Min",
        "max": "Max",
        "sum": "Sum",
        "var": "Variance",
    }
    clabel = operation_labels[operation]

    # Create professional matplotlib figure
    fig, ax = plt.subplots(figsize=(12, 8), dpi=300, facecolor="white")

    # Plot the data
    im = ax.pcolormesh(yearly_agg.x, yearly_agg.y, yearly_agg, cmap="YlOrRd_r", shading="auto")

    # Add grid
    ax.grid(True, alpha=0.3)

    # Customize colorbar
    cbar = plt.colorbar(im, ax=ax, shrink=0.8, pad=0.02, aspect=20)
    cbar.set_label(clabel, fontsize=10, weight="bold")

    # Dynamic title using varname
    title_text = (
        f"{varname.title()} {clabel}: {year} | {calendar.month_name[month_start]}–{calendar.month_name[month_end]}"
    )
    ax.set_title(title_text, fontsize=14, weight="bold", pad=20)

    # Set labels
    ax.set_xlabel("X coordinate")
    ax.set_ylabel("Y coordinate")

    # Adjust layout and save
    plt.tight_layout()
    plt.savefig("output.png", dpi=300, bbox_inches="tight", facecolor="white")
    plt.close()

    image_url = upload_image_to_imgbb("output.png")
    return f"![{varname} plot using virtual access]({image_url})"


def list_datasets():
    if ds:
        vars = ds.vars
        return vars
    else:
        return "Not initialized"


def init_cluster():
    ea.login()
    client, cluster = create_dask_cluster(n_workers=16)
    client.run(silence_worker_warnings)


def get_smap_dataset() -> xr.Dataset:
    refs = "https://its-live-data.s3-us-west-2.amazonaws.com/test-space/vds/SPL4SMGP.parquet"
    daac_fs = ea.get_fsspec_https_session()

    fs = fsspec.filesystem(
        "reference",
        fo=refs,
        remote_protocol="https",
        asynchronous=True,
        remote_options={"asynchronous": True, **daac_fs.storage_options},
    )

    store = zarr.storage.FsspecStore(fs, read_only=True)
    ds = xr.open_zarr(store, consolidated=False)
    return ds
