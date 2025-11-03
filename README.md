# midstac

## Overview

MCP (Model Context Protocol) server that uses `earthaccess` and `pystac_client` to dispatch queries by extracting spatiotemporal parameters from natural language. It also has proof-of-concept endpoints to plot SMAP data using virtual access patterns.

## Installation

```bash
pip install -e .
```

For development:

```bash
pip install -e ".[dev]"
```

## Configuration

### NASA Earthdata Credentials

For NASA Earthdata access, you need to register at <https://urs.earthdata.nasa.gov/> and set environment variables:

```bash
export EARTHDATA_TOKEN="your_token"
```

Or create a `.env` file.

### MCP Client Configuration

To use midstac with an MCP client (like Claude Desktop), add to your MCP configuration file:

```json
{
  "mcpServers": {
    "midstac": {
      "command": "python",
      "args": ["-m", "midstac.server"],
      "env": {
        "EARTHDATA_TOKEN": "your_token",
        "IMGBB_API_KEY": "your_imgbb_key",
        "GEOAPI_KEY": "your_geoapi_key"
      }
    }
  }
}
```

See `mcp-config.example.json` for a complete example.

For the demo, we use OpenWeb UI, we can start it using the docker compose file:

```bash
docker-compose -f docker-compose.yml up
```

## Usage

### Running the MCP Server

```bash
midstac
```

Or directly with Python:

```bash
python -m midstac.server
```

Or if used with mcpo:

```bash
mcpo --hot-reload --cors-allow-origins "*" --port 8000 -- midstac
```

### Available Tools

The server exposes the following tools via MCP:

#### `query_earth_collections`

Main query interface that accepts natural language and returns results from multiple sources (NASA and other STAC sources).

Example queries:

- "Find Landsat data over California from 2020 to 2021"
- "Show me MODIS imagery near 37.7749, -122.4194 from last month"
- "Get satellite data in bbox [-122.5, 37.5, -122.0, 38.0] from 2022"
- "I would like NASA data for wildfires in Australia between 2019 and 2020"
- "List 10 GEDI datasets in your STAC catalog over the Amazon forest"

#### `earthaccess_api`

Returns a consolidated API documentation for the `earthaccess` library. This teaches the agent how to build programmatic access scripts.

#### `plot_smap_area`

Subsets a request to plot SMAP data over a specified area and time range. Returns a markdown link to the generated plot.
Uses the new virtual access pattern for SMAP L4 data, a new `earthaccess`` feature in`v0.15.1`.

## Examples

### Natural Language Query

```python
from midstac.server import query_earth_data

results = query_earth_data("Find satellite imagery over New York from last week")
print(results)
```

### Parameter Extraction

```python
from midstac.extractor import SpatiotemporalExtractor

extractor = SpatiotemporalExtractor()
params = extractor.extract_parameters(
    "Show me data over San Francisco between 2020-01-01 and 2020-12-31"
)
print(params)
# Output: {
#     'query': 'Show me data over San Francisco between 2020-01-01 and 2020-12-31',
#     'location': 'San Francisco',
#     'temporal': {'start_date': '2020-01-01', 'end_date': '2020-12-31'}
# }
```

### Direct STAC Search

```python
from midstac.dispatcher import QueryDispatcher

dispatcher = QueryDispatcher()
items = dispatcher.search_stac(
    bbox=(-122.5, 37.5, -122.0, 38.0),
    datetime="2020-01-01/2020-12-31",
    limit=5
)
print(f"Found {len(items)} items")
```

## License

GPL-3.0 license
