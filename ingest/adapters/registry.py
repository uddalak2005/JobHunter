from ingest.adapters.greenhouse import GreenhouseAdapter
from ingest.adapters.ashby import AshbyAdapter
from ingest.adapters.lever import LeverAdapter


class AdapterRegistry:
    """A registry for managing and retrieving adapter instances."""

    def __init__(self):
        self.adapters = {
            "greenhouse": GreenhouseAdapter(),
            "ashby": AshbyAdapter(),
            "lever": LeverAdapter(),
        }

    def get_adapter(self, provider: str):
        adapter = self.adapters.get(provider)
        if not adapter:
            raise ValueError(f"No adapter found for provider: {provider}")
        return adapter
