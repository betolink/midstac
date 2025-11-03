from midstac.extractor import SpatiotemporalExtractor


class TestSpatiotemporalExtractor:
    """Test the SpatiotemporalExtractor class"""

    def setup_method(self):
        """Set up test fixtures"""
        self.extractor = SpatiotemporalExtractor()

    def test_extract_location(self):
        """Test location extraction"""
        # Test basic location extraction
        query = "Find data in California"
        location = self.extractor.extract_location(query)
        assert location == "California"

        # Test location with multiple words
        query = "Show me imagery over New York"
        location = self.extractor.extract_location(query)
        assert location == "New York"

        # Test no location
        query = "Find some data"
        location = self.extractor.extract_location(query)
        assert location is None

    def test_extract_coordinates(self):
        """Test coordinate extraction"""
        # Test basic coordinate pattern
        query = "Data at 37.7749, -122.4194"
        coords = self.extractor.extract_coordinates(query)
        assert coords == (37.7749, -122.4194)

        # Test latitude/longitude pattern
        query = "lat: 40.7128, lon: -74.0060"
        coords = self.extractor.extract_coordinates(query)
        assert coords == (40.7128, -74.0060)

        # Test invalid coordinates
        query = "Data at 200, 300"
        coords = self.extractor.extract_coordinates(query)
        assert coords is None

    def test_extract_bbox(self):
        """Test bounding box extraction"""
        # Test bbox pattern
        query = "bbox: [-122.5, 37.5, -122.0, 38.0]"
        bbox = self.extractor.extract_bbox(query)
        assert bbox == (-122.5, 37.5, -122.0, 38.0)

        # Test bounds pattern
        query = "bounds = -180, -90, 180, 90"
        bbox = self.extractor.extract_bbox(query)
        assert bbox == (-180.0, -90.0, 180.0, 90.0)

    def test_extract_temporal(self):
        """Test temporal extraction"""
        # Test date range with 'from...to'
        query = "from 2020-01-01 to 2020-12-31"
        temporal = self.extractor.extract_temporal(query)
        assert temporal is not None
        assert temporal["start_date"] == "2020-01-01"
        assert temporal["end_date"] == "2020-12-31"

        # Test date range with 'between...and'
        query = "between 2019-06-01 and 2019-06-30"
        temporal = self.extractor.extract_temporal(query)
        assert temporal is not None
        assert temporal["start_date"] == "2019-06-01"
        assert temporal["end_date"] == "2019-06-30"

        # Test year only
        query = "in 2021"
        temporal = self.extractor.extract_temporal(query)
        assert temporal is not None
        assert temporal["start_date"] == "2021-01-01"
        assert temporal["end_date"] == "2021-12-31"
