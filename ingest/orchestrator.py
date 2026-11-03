from ingest.adapters.registry import AdapterRegistry
import httpx
from ingest.schemas import ATSBoard, NormalizedJob

class IngestionService:
    def __init__(self, registry: AdapterRegistry):
        self.registry = registry
        
    async def ingest(self, boards : list[ATSBoard], client : httpx.AsyncClient):
        
        alljobs : list[NormalizedJob] = []
        
        for board in boards:
            
            adapter = self.registry.get_adapter(board.provider)

            jobs = await adapter.fetch_jobs(board, client)
            
            alljobs.extend(jobs)
            
        return alljobs