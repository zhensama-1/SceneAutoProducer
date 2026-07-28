from __future__ import annotations

from src.asset_retrieval import AssetRetriever, AssetStrategyPlanner


class Step3AssetEnrichmentOrchestrator:
    def __init__(self, retriever: AssetRetriever | None = None, strategy_planner: AssetStrategyPlanner | None = None):
        self.retriever = retriever
        self.strategy_planner = strategy_planner or AssetStrategyPlanner()
