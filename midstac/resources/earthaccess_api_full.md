# earthaccess API

earthaccess is a Python library that simplifies data discovery and access to NASA Earth science data by providing a higher abstraction for NASA’s Search API (CMR) so that searching for data can be done using a simpler notation instead of low level HTTP queries.
This library handles authentication with NASA’s OAuth2 API (EDL) and provides HTTP and AWS S3 sessions that can be used with xarray and other PyData libraries to access NASA EOSDIS datasets directly allowing scientists get to their science in a simpler and faster way, reducing barriers to cloud-based data analysis.

##  `download(granules, local_path=None, provider=None, threads=8, *, show_progress=None, credentials_endpoint=None, pqdm_kwargs=None)`

Retrieves data granules from a remote storage system. Provide the optional `local_path` argument to prevent repeated downloads.

- If we run this in the cloud, we will be using S3 to move data to `local_path`.
- If we run it outside AWS (us-west-2 region) and the dataset is cloud hosted, we'll use HTTP links.

**Parameters:**

Name | Type | Description | Default
---|---|---|---
`granules` | `Union[DataGranule, List[DataGranule], str, List[str]]` | a granule, list of granules, a granule link (HTTP), or a list of granule links (HTTP) | required
`local_path` | `Optional[Union[Path, str]]` | Local directory to store the remote data granules. If not supplied, defaults to a subdirectory of the current working directory of the form `data/YYYY-MM-DD-UUID`, where `YYYY-MM-DD` is the year, month, and day of the current date, and `UUID` is the last 6 digits of a UUID4 value. | `None`
`provider` | `Optional[str]` | if we download a list of URLs, we need to specify the provider. | `None`
`credentials_endpoint` | `Optional[str]` | S3 credentials endpoint to be used for obtaining temporary S3 credentials. This is only required if the metadata doesn't include it, or we pass urls to the method instead of `DataGranule` instances. | `None`
`threads` | `int` | parallel number of threads to use to download the files, adjust as necessary, default = 8 | `8`
`show_progress` | `Optional[bool]` | whether or not to display a progress bar. If not specified, defaults to `True` for interactive sessions (i.e., in a notebook or a python REPL session), otherwise `False`. | `None`
`pqdm_kwargs` | `Optional[Mapping[str, Any]]` | Additional keyword arguments to pass to pqdm, a parallel processing library. See pqdm documentation for available options. Default is to use immediate exception behavior and the number of jobs specified by the `threads` parameter. | `None`

**Returns:**

Type | Description
---|---
`List[Path]` | List of downloaded files

**Raises:**

Type | Description
---|---
`Exception` | A file download failed.

##  `get_edl_token()`

Returns the current token used for EDL.

**Returns:**

Type | Description
---|---
`str` | EDL token


##  `open(granules, provider=None, *, credentials_endpoint=None, show_progress=None, pqdm_kwargs=None, open_kwargs=None)`

Returns a list of file-like objects that can be used to access files hosted on S3 or HTTPS by third party libraries like xarray.

**Parameters:**

Name | Type | Description | Default
---|---|---|---
`granules` | `Union[List[str], List[DataGranule]]` | a list of granule instances or list of URLs, e.g. `s3://some-granule`. If a list of URLs is passed, we need to specify the data provider. | required
`provider` | `Optional[str]` | e.g. POCLOUD, NSIDC_CPRD, etc. | `None`
`show_progress` | `Optional[bool]` | whether or not to display a progress bar. If not specified, defaults to `True` for interactive sessions (i.e., in a notebook or a python REPL session), otherwise `False`. | `None`
`pqdm_kwargs` | `Optional[Mapping[str, Any]]` | Additional keyword arguments to pass to pqdm, a parallel processing library. See pqdm documentation for available options. Default is to use immediate exception behavior and the number of jobs specified by the `threads` parameter. | `None`
`open_kwargs` | `Optional[Dict[str, Any]]` | Additional keyword arguments to pass to `fsspec.open`, such as `cache_type` and `block_size`. Defaults to using `blockcache` with a block size determined by the file size (4 to 16MB). | `None`

**Returns:**

Type | Description
---|---
`List[AbstractFileSystem]` | A list of "file pointers" to remote (i.e. s3 or https) files.

##  `search_data(count=-1, **kwargs)`

Search for dataset files (granules) using NASA's CMR.

https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html

The CMR does not permit queries across all granules in all collections in order to provide fast search responses. Granule queries must target a subset of the collections in the CMR using a condition like provider, provider_id, concept_id, collection_concept_id, short_name, version or entry_title.

**Parameters:**

Name | Type | Description | Default
---|---|---|---
`count` | `int` | Number of records to get, -1 = all | `-1`
`kwargs` | `Dict` | arguments to CMR: <br> * short_name: (str) Filter granules by product short name; e.g. ATL08 <br> * version: (str) Filter by dataset version <br> * daac: (str) a provider code for any DAAC, e.g. NSIDC or PODAAC <br> * data_center; (str) An alias for daac <br> * provider: (str) Only match granules from a given provider. A DAAC can have more than one provider, e.g PODAAC and POCLOUD, NSIDC_ECS and NSIDC_CPRD. <br> * cloud_hosted: (bool) If True, only match granules hosted in Earthdata Cloud <br> * downloadable: (bool) If True, only match granules that are downloadable. A granule is downloadable when it contains at least one RelatedURL of type GETDATA. <br> * online_only: (bool) Alias of downloadable <br> * orbit_number; (float) Filter granule by the orbit number in which a granule was acquired <br> * granule_name; (str) Filter by granule name. Granule name can contain wild cards, e.g `MODGRNLD.*.daily.*`. <br> * instrument; (str) Filter by instrument name, e.g. "ATLAS" <br> * platform; (str) Filter by platform, e.g. satellite or plane <br> * cloud_cover: (tuple) Filter by cloud cover. Tuple is a range of cloud covers, e.g. (0, 20). Cloud cover values in metadata may be fractions (i.e. (0.,0.2)) or percentages. CMRS searches for cloud cover range based on values in metadata. Note collections without cloud_cover in metadata will return zero granules. <br> * day_night_flag: (str) Filter for day- and night-time images, accepts 'day', 'night', 'unspecified'. <br> * temporal: (tuple) A tuple representing temporal bounds in the form `(date_from, date_to)`. Dates can be `datetime` objects or ISO 8601 formatted strings. Date strings can be full timestamps; e.g. YYYY-MM-DD HH:mm:ss or truncated YYYY-MM-DD <br> * bounding_box: (tuple) Filter collection by those that intersect bounding box. A tuple representing spatial bounds in the form `(lower_left_lon, lower_left_lat, upper_right_lon, upper_right_lat)` <br> * polygon: (list[tuples]) Filter by polygon. Polygon must be a list of tuples containing longitude-latitude pairs representing polygon vertices. Vertices must be in counter-clockwise order and the final vertex must be the same as the first vertex; e.g. [(lon1,lat1),(lon2,lat2),(lon3,lat3), (lon4,lat4),(lon1,lat1)] <br> * point: (tuple(float,float)) Filter by collections intersecting a point, where the point is a longitude-latitude pair; e.g. (lon,lat) <br> * line: (list[tuples]) Filter collections that overlap a series of connected points. Points are represented as tuples containing longitude-latitude pairs; e.g. [(lon1,lat1),(lon2,lat2),(lon3,lat3)] <br> * circle: (tuple(float, float, float)) Filter collections that intersect a circle defined as a point with a radius. Circle parameters are a tuple containing latitude, longitude and radius in meters; e.g. (lon, lat, radius_m). The circle center cannot be the north or south poles. The radius mst be between 10 and 6,000,000 m | `{}`

**Returns:**

Type | Description
---|---
`List[DataGranule]` | a list of DataGranules that can be used to access the granule files by using `download()` or `open()`.

**Raises:**

Type | Description
---|---
`RuntimeError` | The CMR query failed.

**Examples:**

```python
granules = earthaccess.search_data(
    short_name="ATL06",
    bounding_box=(-46.5, 61.0, -42.5, 63.0),
)
granules = earthaccess.search_data(
    concept_id="c1233434-nsidc",
    cloud_hosted=True,
    temporal=("2002-01-01","2002-12-31")
)
```

##  `search_datasets(count=-1, **kwargs)`

Search datasets (collections) using NASA's CMR.

https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html

**Parameters:**

Name | Type | Description | Default
---|---|---|---
`count` | `int` | Number of records to get, -1 = all | `-1`
`kwargs` | `Dict` | arguments to CMR: <br> * keyword: (str) Filter collections by keywords. Case-insensitive and supports wildcards ? and * <br> * short_name: (str) Filter collections by product short name; e.g. ATL08 <br> * doi: (str) Filter by DOI <br> * daac: (str) Filter by DAAC; e.g. NSIDC or PODAAC <br> * data_center: (str) An alias for `daac` <br> * provider: (str) Filter by data provider; each DAAC can have more than one provider, e.g. POCLOUD, PODAAC, etc. <br> * has_granules: (bool) If true, only return collections with granules. Default: True <br> * temporal: (tuple) A tuple representing temporal bounds in the form `(date_from, date_to)`. Dates can be `datetime` objects or ISO 8601 formatted strings. Date strings can be full timestamps; e.g. YYYY-MM-DD HH:mm:ss or truncated YYYY-MM-DD <br> * bounding_box: (tuple) Filter collection by those that intersect bounding box. A tuple representing spatial bounds in the form `(lower_left_lon, lower_left_lat, upper_right_lon, upper_right_lat)` <br> * polygon: (List[tuples]) Filter by polygon. Polygon must be a list of tuples containing longitude-latitude pairs representing polygon vertices. Vertices must be in counter-clockwise order and the final vertex must be the same as the first vertex; e.g. `[(lon1,lat1),(lon2,lat2),(lon3,lat3),(lon4,lat4),(lon1,lat1)]` <br> * point: (Tuple[float,float]) Filter by collections intersecting a point, where the point is a longitude-latitude pair; e.g. `(lon,lat)` <br> * line: (List[tuples]) Filter collections that overlap a series of connected points. Points are represented as tuples containing longitude-latitude pairs; e.g. `[(lon1,lat1),(lon2,lat2),(lon3,lat3)]` <br> * circle: (List[float, float, float]) Filter collections that intersect a circle defined as a point with a radius. Circle parameters are a list containing latitude, longitude and radius in meters; e.g. `[lon, lat, radius_m]`. The circle center cannot be the north or south poles. The radius mst be between 10 and 6,000,000 m <br> * cloud_hosted: (bool) Return only collected hosted on Earthdata Cloud. Default: True <br> * downloadable: (bool) If True, only return collections that can be downloaded from an online archive <br> * concept_id: (str) Filter by Concept ID; e.g. C3151645377-NSIDC_CPRD <br> * instrument: (str) Filter by Instrument name; e.g. ATLAS <br> * project: (str) Filter by project or campaign name; e.g. ABOVE <br> * fields: (List[str]) Return only the UMM fields listed in this parameter <br> * revision_date: tuple(str,str) Filter by collections that have revision date within the range <br> * debug: (bool) If True prints CMR request. Default: True | `{}`

**Returns:**

Type | Description
---|---
`List[DataCollection]` | A list of DataCollection results that can be used to get information about a dataset, e.g. concept_id, doi, etc.

**Raises:**

Type | Description
---|---
`RuntimeError` | The CMR query failed.

**Examples:**

```python
datasets = earthaccess.search_datasets(
    keyword="sea surface anomaly",
    cloud_hosted=True
)

results = earthaccess.search_datasets(
    daac="NSIDC",
    bounding_box=(-73., 58., -10., 84.),
)

results = earthaccess.search_datasets(
    instrument="ATLAS",
    bounding_box=(-73., 58., -10., 84.),
    temporal=("2024-09-01","2025-04-30"),
)
```

##  `search_services(count=-1, **kwargs)`

Search the NASA CMR for Services matching criteria.

See https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html#service.

**Parameters:**

Name | Type | Description | Default
---|---|---|---
`count` | `int` | maximum number of services to fetch (if less than 1, all services matching specified criteria are fetched [default]) | `-1`
`kwargs` | `Any` | keyword arguments accepted by the CMR for searching services | `{}`

**Returns:**

Type | Description
---|---
`List[Any]` | list of services (possibly empty) matching specified criteria, in UMM

**Examples:**

```python
services = search_services(provider="POCLOUD", keyword="COG")
```

##  `status(system=PROD, raise_on_outage=False)`

Get the statuses of NASA's Earthdata services.

**Parameters:**

Name | Type | Description | Default
---|---|---|---
`system` | `System` | The Earthdata system to access, defaults to PROD. | `PROD`
`raise_on_outage` | `bool` | If True, raises exception on errors or outages. | `False`

**Returns:**

Type | Description
---|---
`dict[str, str]` | A dictionary containing the statuses of Earthdata services.

**Examples:**

```
>>> earthaccess.status()
{'Earthdata Login': 'OK', 'Common Metadata Repository': 'OK'}
>>> earthaccess.status(earthaccess.UAT)
{'Earthdata Login': 'OK', 'Common Metadata Repository': 'OK'}
```

**Raises:**

Type | Description
---|---
`ServiceOutage` | if at least one service status is not `"OK"`


##  `open_virtual_dataset(granule, group=None, access='indirect')`

Open a granule as a single virtual xarray Dataset.

Uses NASA DMR++ metadata files to create a virtual xarray dataset with ManifestArrays. This virtual dataset can be used to create zarr reference files. See https://virtualizarr.readthedocs.io for more information on virtual xarray datasets.

> **Warning**
> This feature is current experimental and may change in the future. This feature relies on DMR++ metadata files which may not always be present for your dataset and you may get a `FileNotFoundError`.

**Parameters:**

Name | Type | Description | Default
---|---|---|---
`granule` | `DataGranule` | The granule to open | required
`group` | `str \| None` | Path to the netCDF4 group in the given file to open. If None, the root group will be opened. If the DMR++ file does not have groups, this parameter is ignored. | `None`
`access` | `str` | The access method to use. One of "direct" or "indirect". Use direct when running on AWS, use indirect when running on a local machine. | `'indirect'`

**Returns:**

Type | Description
---|---
`Dataset` | xarray.Dataset

**Examples:**

```python
>>> results = earthaccess.search_data(count=2, temporal=("2023"), short_name="SWOT_L2_LR_SSH_Expert_2.0")
>>> vds =  earthaccess.open_virtual_dataset(results[0], access="indirect")
>>> vds
<xarray.Dataset> Size: 149 MB
Dimensions:                                (num_lines: 9866, num_pixels: 69,
                                                num_sides: 2)
Coordinates:
    longitude                              (num_lines, num_pixels) int32 3 MB ...
    latitude                               (num_lines, num_pixels) int32 3 MB ...
    latitude_nadir                         (num_lines) int32 39 kB ManifestArr...
    longitude_nadir                        (num_lines) int32 39 kB ManifestArr...
Dimensions without coordinates: num_lines, num_pixels, num_sides
Data variables: (12/98)
    height_cor_xover_qual                  (num_lines, num_pixels) uint8 681 kB ManifestArray<shape=(9866, 69), dtype=uint8, chunks=(9866, 69...
>>> vds.virtualize.to_kerchunk("swot_2023_ref.json", format="json")
```

##  `open_virtual_mfdataset(granules, group=None, access='indirect', preprocess=None, parallel='dask', load=True, reference_dir=None, reference_format='json', **xr_combine_nested_kwargs)`

Open multiple granules as a single virtual xarray Dataset.
Uses NASA DMR++ metadata files to create a virtual xarray dataset with ManifestArrays. This virtual dataset can be used to create zarr reference files. See https://virtualizarr.readthedocs.io for more information on virtual xarray datasets.

> **Warning**
> This feature is current experimental and may change in the future. This feature relies on DMR++ metadata files which may not always be present for your dataset and you may get a `FileNotFoundError`.

**Parameters:**

Name | Type | Description | Default
---|---|---|---
`granules` | `list[DataGranule]` | The granules to open | required
`group` | `str \| None` | Path to the netCDF4 group in the given file to open. If None, the root group will be opened. If the DMR++ file does not have groups, this parameter is ignored. | `None`
`access` | `str` | The access method to use. One of "direct" or "indirect". Use direct when running on AWS, use indirect when running on a local machine. | `'indirect'`
`preprocess` | `callable \| None` | A function to apply to each virtual dataset before combining | `None`
`parallel` | `Literal['dask', 'lithops', False]` | Open the virtual datasets in parallel (using dask.delayed or lithops) | `'dask'`
`load` | `bool` | If load is True, earthaccess will serialize the virtual references in order to use lazy indexing on the resulting xarray virtual ds. | `True`
`reference_dir` | `str \| None` | Directory to store kerchunk references. If None, a temporary directory will be created and deleted after use. | `None`
`reference_format` | `Literal['json', 'parquet']` | When load is True, earthaccess will serialize the references using this format, json (default) or parquet. | `'json'`
`xr_combine_nested_kwargs` | `Any` | Xarray arguments describing how to concatenate the datasets. Keyword arguments for xarray.combine_nested. See https://docs.xarray.dev/en/stable/generated/xarray.combine_nested.html | `{}`

**Returns:**

Type | Description
---|---
`Dataset` | Concatenated xarray.Dataset

**Examples:**

```python
>>> results = earthaccess.search_data(count=5, temporal=("2024"), short_name="MUR-JPL-L4-GLOB-v4.1")
>>> vds = earthaccess.open_virtual_mfdataset(results, access="indirect", load=False, concat_dim="time", coords="minimal", compat="override", combine_attrs="drop_conflicts")
>>> vds
<xarray.Dataset> Size: 29 GB
Dimensions:           (time: 5, lat: 17999, lon: 36000)
Coordinates:
    time              (time) int32 20 B ManifestArray<shape=(5,), dtype=int32,...
    lat               (lat) float32 72 kB ManifestArray<shape=(17999,), dtype=...
    lon               (lon) float32 144 kB ManifestArray<shape=(36000,), dtype...
Data variables:
    mask              (time, lat, lon) int8 3 GB ManifestArray<shape=(5, 17999...
    sea_ice_fraction  (time, lat, lon) int8 3 GB ManifestArray<shape=(5, 17999...
    dt_1km_data       (time, lat, lon) int8 3 GB ManifestArray<shape=(5, 17999...
    analysed_sst      (time, lat, lon) int16 6 GB ManifestArray<shape=(5, 1799...
    analysis_error    (time, lat, lon) int16 6 GB ManifestArray<shape=(5, 1799...
    sst_anomaly       (time, lat, lon) int16 6 GB ManifestArray<shape=(5, 1799...
Attributes: (12/42)
    Conventions:                CF-1.7
    title:                      Daily MUR SST, Final product
>>> vds.virtualize.to_kerchunk("mur_combined.json", format="json")
>>> vds = open_virtual_mfdataset(results, access="indirect", concat_dim="time", coords='minimal', compat='override', combine_attrs="drop_conflicts")
>>> vds
<xarray.Dataset> Size: 143 GB
Dimensions:           (time: 5, lat: 17999, lon: 36000)
Coordinates:
    * lat               (lat) float32 72 kB -89.99 -89.98 -89.97 ... 89.98 89.99
    * lon               (lon) float32 144 kB -180.0 -180.0 -180.0 ... 180.0 180.0
    * time              (time) datetime64[ns] 40 B 2024-01-01 T09:00:00 ... 2024-...
Data variables:
    analysed_sst      (time, lat, lon) float64 26 GB dask.array<chunksize=(1, 3600, 7200), meta=np.ndarray>
    analysis_error    (time, lat, lon) float64 26 GB dask.array<chunksize=(1, 3600, 7200), meta=np.ndarray>
    dt_1km_data       (time, lat, lon) timedelta64[ns] 26 GB dask.array<chunksize=(1, 4500, 9000), meta=np.ndarray>
    mask              (time, lat, lon) float32 13 GB dask.array<chunksize=(1, 4500, 9000), meta=np.ndarray>
    sea_ice_fraction  (time, lat, lon) float64 26 GB dask.array<chunksize=(1, 4500, 9000), meta=np.ndarray>
    sst_anomaly       (time, lat, lon) float64 26 GB dask.array<chunksize=(1, 3600, 7200), meta=np.ndarray>
Attributes: (12/42)
    Conventions:                CF-1.7
    title:                      Daily MUR SST, Final product
