from midstac.dispatcher import QueryDispatcher


class TestQueryDispatcher:
    """Test the QueryDispatcher class"""

    def setup_method(self):
        """Set up test fixtures"""
        self.dispatcher = QueryDispatcher()

    def test_dispatcher_initialization(self):
        """Test dispatcher initializes correctly"""
        assert self.dispatcher is not None
        # Authentication may succeed if credentials are available in environment
        # This is expected behavior in real usage
        assert self.dispatcher.auth is not None

    def test_stac_catalogs_defined(self):
        """Test STAC catalog URLs are defined"""
        assert "nasa" in self.dispatcher.STAC_CATALOGS
        assert "earth_search" in self.dispatcher.STAC_CATALOGS
        assert "planetary_computer" in self.dispatcher.STAC_CATALOGS
