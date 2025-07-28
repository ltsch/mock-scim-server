"""
Centralized server context management for multi-server support.

This module provides a unified interface for extracting server IDs from different
sources (query parameters, path parameters, headers, etc.) and can be easily
extended to support new routing strategies.
"""

from fastapi import Request, Path
from typing import Optional, Callable, Dict, Any
from loguru import logger
from enum import Enum

class ServerIdSource(Enum):
    PATH_PARAM = "path_param"

class ServerContextManager:
    def __init__(self, default_source: ServerIdSource = ServerIdSource.PATH_PARAM):
        self.default_source = default_source
        self.extractors: Dict[ServerIdSource, Callable] = {
            ServerIdSource.PATH_PARAM: self._extract_from_path_param,
        }
        self.custom_extractors: Dict[str, Callable] = {}

    def register_custom_extractor(self, name: str, extractor: Callable):
        self.custom_extractors[name] = extractor
        logger.info(f"Registered custom server ID extractor: {name}")

    def _extract_from_path_param(self, server_id: str = Path(..., description="Server identifier")) -> str:
        logger.info(f"Using server ID from path: {server_id}")
        return server_id

    def get_extractor(self, source: Optional[ServerIdSource] = None) -> Callable:
        source = source or self.default_source
        extractor = self.extractors.get(source)
        if not extractor:
            raise ValueError(f"Unknown server ID source: {source}")
        return extractor

    def create_dependency(self, source: Optional[ServerIdSource] = None) -> Callable:
        return self.get_extractor(source)

def get_server_id_from_path(server_id: str = Path(..., description="Server identifier")) -> str:
    return server_id

def configure_server_id_source(source: ServerIdSource):
    # Only path param is supported
    logger.info(f"Configured server ID extraction to use: {source.value}") 