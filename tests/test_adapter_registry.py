from ingest.adapters.registry import AdapterRegistry

def test_get_adapter_success():
    registry = AdapterRegistry()
    
    # Test for GreenhouseAdapter
    greenhouse_adapter = registry.get_adapter("greenhouse")
    assert greenhouse_adapter.__class__.__name__ == "GreenhouseAdapter"
    
    # Test for AshbyAdapter
    ashby_adapter = registry.get_adapter("ashby")
    assert ashby_adapter.__class__.__name__ == "AshbyAdapter"
    
    # Test for LeverAdapter
    lever_adapter = registry.get_adapter("lever")
    assert lever_adapter.__class__.__name__ == "LeverAdapter"