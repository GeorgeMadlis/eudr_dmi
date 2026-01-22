# Prompts Metadata

This directory contains governance, usage rules, and evolution notes for operational prompts.

## Purpose

- **Usage Rules**: How prompts should be interpreted and executed by Copilot
- **Safety Rules**: Guardrails and validation requirements
- **Evolution Notes**: Changelog of prompt modifications and why

## Principles

1. **Prompts are procedural instructions**, not scripts to be blindly executed
2. **Host-specific awareness**: Prompts must detect and adapt to environment (Mac mini vs laptop)
3. **Version control**: All changes must be tracked with clear rationale
4. **Review required**: Prompts are code - they need review before execution

## Host Detection

Prompts should detect the host environment:
- **Mac mini** (headless server): `/Users/server/projects/geospatial_dmi`
- **MacBook Pro** (dev laptop): Different path if applicable

Use this detection to adjust:
- Resource allocation (CPU/memory for containers)
- Network endpoints
- Storage paths
- Parallelism settings
