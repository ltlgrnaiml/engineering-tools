# Engineering Tools Platform - Process Definitions
# =================================================
# Per ADR-0037: Single-Command Development Environment
# 
# Usage:
#   honcho start              # Start all services
#   honcho start backend      # Start only backend
#   honcho start backend dat  # Start backend + DAT frontend
#
# Port Assignments (per SPEC-0045):
#   Backend Gateway:  8000
#   MkDocs:           8001
#   Homepage:         3000
#   DAT Frontend:     5173
#   SOV Frontend:     5174
#   PPTX Frontend:    5175

backend: python -m uvicorn gateway.main:app --host 0.0.0.0 --port 8000 --reload
mkdocs: mkdocs serve --dev-addr 127.0.0.1:8001
homepage: npm run dev --prefix apps/homepage/frontend -- --port 3000 --host
dat: npm run dev --prefix apps/data_aggregator/frontend -- --port 5173 --host
sov: npm run dev --prefix apps/sov_analyzer/frontend -- --port 5174 --host
pptx: npm run dev --prefix apps/pptx_generator/frontend -- --port 5175 --host
