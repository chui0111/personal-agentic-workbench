"""Offline, privacy-safe workflow demonstration."""

from .core import (MockAgent, LocalMockSink, Pipeline, atomic_json, canonical_url,
                   load_json, stable_id, validate_job, build_brief)

__all__ = ["MockAgent", "LocalMockSink", "Pipeline", "atomic_json",
           "canonical_url", "load_json", "stable_id", "validate_job", "build_brief"]
