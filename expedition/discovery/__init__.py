"""Agentic discovery harness: seed → hop → merge. Not a listing service."""

from expedition.discovery.harness import run_discovery
from expedition.discovery.router import plan_sources

__all__ = ["run_discovery", "plan_sources"]
