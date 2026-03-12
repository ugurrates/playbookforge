"""
PlaybookForge - FastAPI Backend
REST API for CACAO playbook conversion, validation, and management.
"""

from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import Any, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel

logger = logging.getLogger(__name__)

from .core.cacao_model import CacaoPlaybook
from .core.validator import CacaoValidator
from .core.builder import PlaybookBuilder
from .exporters import registry as exporter_registry
from .importers import importer_registry
from .llm import get_llm_client
from .db.library import library as playbook_library, PlaybookEntry
from .core.products import product_catalog
from .core.integrations import integration_client
from .pdf.generator import pdf_generator
from .pdf.file_storage import file_storage
from .core.resources import resource_catalog
from .core.repo_manager import repo_manager

# ============================================================================
# App Lifespan (startup/shutdown)
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Validate critical resources on startup, clean up on shutdown."""
    # --- STARTUP ---
    checks_passed = 0
    total_checks = 0

    # Check library directory
    total_checks += 1
    try:
        lib_dir = playbook_library.library_dir
        if lib_dir.exists() and os.access(lib_dir, os.W_OK):
            checks_passed += 1
            logger.info("✓ Library directory writable: %s", lib_dir)
        else:
            logger.error("✗ Library directory not writable: %s", lib_dir)
    except Exception as e:
        logger.error("✗ Library directory check failed: %s", e)

    # Check file storage directory
    total_checks += 1
    try:
        fs_dir = file_storage.storage_dir
        if fs_dir.exists() and os.access(fs_dir, os.W_OK):
            checks_passed += 1
            logger.info("✓ File storage directory writable: %s", fs_dir)
        else:
            logger.error("✗ File storage directory not writable: %s", fs_dir)
    except Exception as e:
        logger.error("✗ File storage directory check failed: %s", e)

    # Check library index integrity
    total_checks += 1
    try:
        count = playbook_library.count()
        checks_passed += 1
        logger.info("✓ Library index loaded: %d playbooks", count)
    except Exception as e:
        logger.error("✗ Library index corrupted: %s", e)

    logger.info(
        "Startup validation: %d/%d checks passed",
        checks_passed, total_checks,
    )

    # Auto-sync community playbook repos (background)
    auto_sync = os.environ.get("PLAYBOOKFORGE_AUTO_SYNC", "false").lower()
    if auto_sync in ("1", "true", "yes"):
        logger.info("Auto-syncing community playbook repos in background...")
        repo_manager.sync_all(background=True)

    yield  # App runs here

    # --- SHUTDOWN ---
    logger.info("PlaybookForge shutting down...")


# ============================================================================
# App Configuration
# ============================================================================

app = FastAPI(
    title="PlaybookForge API",
    description="Universal SOAR Playbook Converter — CACAO v2.0 based",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Request/Response Models
# ============================================================================

class ConvertRequest(BaseModel):
    """Request to convert a CACAO playbook to a vendor format"""
    playbook: dict[str, Any]
    target_platform: str
    options: Optional[dict[str, Any]] = None


class ConvertResponse(BaseModel):
    success: bool
    platform: str
    filename: str
    content: str
    content_type: str


class ValidateRequest(BaseModel):
    playbook: dict[str, Any]


class ValidateResponse(BaseModel):
    valid: bool
    error_count: int
    warning_count: int
    issues: list[dict[str, Any]]
    playbook_summary: dict[str, Any]


class ConvertAllResponse(BaseModel):
    success: bool
    results: dict[str, Any]


class PlaybookSummary(BaseModel):
    id: str
    name: str
    playbook_types: list[str]
    total_steps: int
    step_types: dict[str, int]
    action_steps: int


class ImportRequest(BaseModel):
    content: str
    source_platform: Optional[str] = None


class ImportResponse(BaseModel):
    success: bool
    detected_platform: str
    playbook: dict[str, Any]


class ImportConvertRequest(BaseModel):
    content: str
    source_platform: Optional[str] = None
    target_platform: str


class DetectResponse(BaseModel):
    detected: bool
    platform_id: Optional[str] = None
    platform_name: Optional[str] = None


class AIGenerateRequest(BaseModel):
    prompt: str
    model: str = "auto"
    product_ids: Optional[list[str]] = None


class AIGenerateResponse(BaseModel):
    success: bool
    playbook: dict[str, Any]
    model_used: str


class AIEnrichRequest(BaseModel):
    playbook: dict[str, Any]
    model: str = "auto"


class AIEnrichResponse(BaseModel):
    success: bool
    playbook: dict[str, Any]
    model_used: str


class AIAnalyzeRequest(BaseModel):
    playbook: dict[str, Any]
    model: str = "auto"


class AIAnalyzeResponse(BaseModel):
    success: bool
    analysis: dict[str, Any]
    model_used: str


# ============================================================================
# Health & Info Endpoints
# ============================================================================

@app.get("/")
async def root():
    return {
        "name": "PlaybookForge API",
        "version": "0.1.0",
        "description": "Universal SOAR Playbook Converter",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/platforms")
async def list_platforms():
    """List all supported SOAR platforms"""
    return {
        "exporters": exporter_registry.list_platforms(),
        "importers": importer_registry.list_platforms(),
        "platforms": exporter_registry.list_platforms(),
        "total": len(exporter_registry.list_platforms()),
    }


# ============================================================================
# Validation Endpoints
# ============================================================================

@app.post("/validate", response_model=ValidateResponse)
async def validate_playbook(request: ValidateRequest):
    """Validate a CACAO v2.0 playbook"""
    try:
        playbook = CacaoPlaybook(**request.playbook)
    except Exception as e:
        return ValidateResponse(
            valid=False,
            error_count=1,
            warning_count=0,
            issues=[{
                "severity": "error",
                "code": "PARSE_ERROR",
                "message": str(e),
                "path": "",
            }],
            playbook_summary={},
        )

    validator = CacaoValidator()
    result = validator.validate(playbook)
    return ValidateResponse(**result.to_dict())


# ============================================================================
# Conversion Endpoints
# ============================================================================

@app.post("/convert", response_model=ConvertResponse)
async def convert_playbook(request: ConvertRequest):
    """Convert a CACAO playbook to a specific vendor format"""
    try:
        playbook = CacaoPlaybook(**request.playbook)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid CACAO playbook: {str(e)}")

    exporter = exporter_registry.get(request.target_platform)
    if not exporter:
        available = [p["platform_id"] for p in exporter_registry.list_platforms()]
        raise HTTPException(
            status_code=400,
            detail=f"Unknown platform '{request.target_platform}'. Available: {available}",
        )

    try:
        content = exporter.export(playbook)
        filename = exporter.get_filename(playbook)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")

    content_type = "application/x-yaml" if filename.endswith(".yml") else "application/json"

    return ConvertResponse(
        success=True,
        platform=request.target_platform,
        filename=filename,
        content=content,
        content_type=content_type,
    )


@app.post("/convert/all", response_model=ConvertAllResponse)
async def convert_all(request: ValidateRequest):
    """Convert a CACAO playbook to ALL supported vendor formats"""
    try:
        playbook = CacaoPlaybook(**request.playbook)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid CACAO playbook: {str(e)}")

    results = {}
    for platform in exporter_registry.list_platforms():
        pid = platform["platform_id"]
        try:
            exporter = exporter_registry.get(pid)
            results[pid] = {
                "success": True,
                "content": exporter.export(playbook),
                "filename": exporter.get_filename(playbook),
                "platform_name": platform["platform_name"],
            }
        except Exception as e:
            results[pid] = {
                "success": False,
                "error": str(e),
                "platform_name": platform["platform_name"],
            }

    return ConvertAllResponse(success=True, results=results)


@app.post("/convert/download/{platform_id}")
async def download_converted(platform_id: str, request: ValidateRequest):
    """Convert and download as file"""
    try:
        playbook = CacaoPlaybook(**request.playbook)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid CACAO playbook: {str(e)}")

    exporter = exporter_registry.get(platform_id)
    if not exporter:
        raise HTTPException(status_code=400, detail=f"Unknown platform: {platform_id}")

    content = exporter.export(playbook)
    filename = exporter.get_filename(playbook)
    content_type = "application/x-yaml" if filename.endswith(".yml") else "application/json"

    return Response(
        content=content,
        media_type=content_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ============================================================================
# Playbook Info Endpoints
# ============================================================================

@app.post("/playbook/summary", response_model=PlaybookSummary)
async def playbook_summary(request: ValidateRequest):
    """Get a summary of a CACAO playbook"""
    try:
        playbook = CacaoPlaybook(**request.playbook)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid CACAO playbook: {str(e)}")

    summary = playbook.summary()
    return PlaybookSummary(**summary)


# ============================================================================
# Import Endpoints
# ============================================================================

@app.post("/import", response_model=ImportResponse)
async def import_playbook(request: ImportRequest):
    """Import a vendor playbook and convert to CACAO v2.0"""
    try:
        playbook = importer_registry.parse(request.content, request.source_platform)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Import failed: {str(e)}")

    # Detect which platform was used
    detected = importer_registry.detect(request.content)
    platform_id = detected.platform_id if detected else (request.source_platform or "unknown")

    return ImportResponse(
        success=True,
        detected_platform=platform_id,
        playbook=playbook.model_dump(exclude_none=True),
    )


@app.post("/import/detect", response_model=DetectResponse)
async def detect_format(request: ImportRequest):
    """Auto-detect the format of a vendor playbook"""
    detected = importer_registry.detect(request.content)
    if detected:
        return DetectResponse(
            detected=True,
            platform_id=detected.platform_id,
            platform_name=detected.platform_name,
        )
    return DetectResponse(detected=False)


@app.post("/import/convert", response_model=ConvertResponse)
async def import_and_convert(request: ImportConvertRequest):
    """Import vendor playbook and convert directly to another vendor format"""
    try:
        playbook = importer_registry.parse(request.content, request.source_platform)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Import failed: {str(e)}")

    exporter = exporter_registry.get(request.target_platform)
    if not exporter:
        available = [p["platform_id"] for p in exporter_registry.list_platforms()]
        raise HTTPException(
            status_code=400,
            detail=f"Unknown target platform '{request.target_platform}'. Available: {available}",
        )

    try:
        content = exporter.export(playbook)
        filename = exporter.get_filename(playbook)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

    content_type = "application/x-yaml" if filename.endswith(".yml") else "application/json"

    return ConvertResponse(
        success=True,
        platform=request.target_platform,
        filename=filename,
        content=content,
        content_type=content_type,
    )


# ============================================================================
# AI / LLM Endpoints
# ============================================================================

@app.post("/ai/generate", response_model=AIGenerateResponse)
async def ai_generate(request: AIGenerateRequest):
    """Generate a CACAO playbook from natural language description using AI."""
    try:
        client = get_llm_client(request.model)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"LLM not available: {str(e)}")

    try:
        playbook_dict = await client.generate_playbook(
            request.prompt,
            product_ids=request.product_ids,
        )
        return AIGenerateResponse(
            success=True,
            playbook=playbook_dict,
            model_used=f"{client.name}/{client.model}",
        )
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"Failed to parse LLM output: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI generation failed: {str(e)}")


@app.post("/ai/enrich", response_model=AIEnrichResponse)
async def ai_enrich(request: AIEnrichRequest):
    """Enrich/improve an existing CACAO playbook using AI."""
    try:
        client = get_llm_client(request.model)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"LLM not available: {str(e)}")

    try:
        enriched = await client.enrich_playbook(request.playbook)
        return AIEnrichResponse(
            success=True,
            playbook=enriched,
            model_used=f"{client.name}/{client.model}",
        )
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI enrichment failed: {str(e)}")


@app.post("/ai/analyze", response_model=AIAnalyzeResponse)
async def ai_analyze(request: AIAnalyzeRequest):
    """Analyze a CACAO playbook quality using AI."""
    try:
        client = get_llm_client(request.model)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"LLM not available: {str(e)}")

    try:
        analysis = await client.analyze_playbook(request.playbook)
        return AIAnalyzeResponse(
            success=True,
            analysis=analysis,
            model_used=f"{client.name}/{client.model}",
        )
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI analysis failed: {str(e)}")


# ============================================================================
# Playbook Library Endpoints
# ============================================================================

@app.get("/library")
async def library_list(
    platform: Optional[str] = None,
    search: Optional[str] = None,
    tag: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
):
    """Browse the playbook library with optional filters."""
    # Clamp limit to prevent unbounded queries
    limit = max(1, min(limit, 200))
    offset = max(0, offset)
    return playbook_library.list_all(
        platform=platform,
        search=search,
        tag=tag,
        limit=limit,
        offset=offset,
    )


@app.get("/library/stats")
async def library_stats():
    """Get library statistics."""
    return {
        "total": playbook_library.count(),
        "by_platform": playbook_library.platforms(),
        "top_tags": dict(list(playbook_library.tags().items())[:20]),
    }


@app.get("/library/{playbook_id}")
async def library_get(playbook_id: str):
    """Get a specific playbook from the library (full CACAO JSON included)."""
    entry = playbook_library.get(playbook_id)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Playbook not found: {playbook_id}")
    return entry.to_dict()


# ============================================================================
# Library Save Endpoint
# ============================================================================

class LibrarySaveRequest(BaseModel):
    """Request to save a CACAO playbook to the library."""
    playbook: dict[str, Any]
    source_platform: str = "designer"
    tags: list[str] = []


@app.post("/library")
async def library_save(request: LibrarySaveRequest):
    """Save a CACAO playbook to the library."""
    import uuid as _uuid
    try:
        playbook = CacaoPlaybook(**request.playbook)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid CACAO playbook: {str(e)}")

    validator = CacaoValidator()
    result = validator.validate(playbook)
    if result.error_count > 0:
        raise HTTPException(status_code=400, detail={
            "message": "Playbook has validation errors",
            "errors": [i.to_dict() for i in result.issues if i.severity == "error"],
        })

    mitre = []
    if playbook.external_references:
        for ref in playbook.external_references:
            name = ref.get("name", "")
            if name.startswith("T") and name[1:].replace(".", "").isdigit():
                mitre.append(name)

    entry = PlaybookEntry(
        id=f"lib-{request.source_platform}-{_uuid.uuid4().hex[:12]}",
        name=playbook.name,
        description=playbook.description or "",
        source_platform=request.source_platform,
        source_repo="user-created",
        source_file="",
        playbook_types=[pt.value if hasattr(pt, 'value') else str(pt) for pt in playbook.playbook_types],
        step_count=len(playbook.workflow),
        action_count=sum(1 for s in playbook.workflow.values() if s.type.value == "action"),
        tags=request.tags,
        mitre_techniques=mitre,
        cacao_playbook=playbook.model_dump(mode="json", exclude_none=True),
    )
    playbook_library.add(entry)
    return {"id": entry.id, "success": True}


# ============================================================================
# Product Catalog Endpoints
# ============================================================================

@app.get("/products")
async def products_list(category: Optional[str] = None):
    """List all products, optionally filtered by category."""
    products = product_catalog.list_all(category=category)
    return {
        "total": len(products),
        "products": [
            {
                "id": p.id,
                "name": p.name,
                "vendor": p.vendor,
                "category": p.category.value,
                "description": p.description,
                "auth_types": [a.value for a in p.auth_types],
                "action_count": len(p.actions),
                "logo_abbr": p.logo_abbr,
                "logo_color": p.logo_color,
            }
            for p in products
        ],
    }


@app.get("/products/categories")
async def products_categories():
    """List product categories with counts."""
    return product_catalog.categories()


@app.get("/products/search")
async def products_search(q: str = ""):
    """Search products by name, vendor, or category."""
    if not q:
        return {"total": 0, "products": []}
    products = product_catalog.search(q)
    return {
        "total": len(products),
        "products": [
            {
                "id": p.id,
                "name": p.name,
                "vendor": p.vendor,
                "category": p.category.value,
                "description": p.description,
                "action_count": len(p.actions),
                "logo_abbr": p.logo_abbr,
                "logo_color": p.logo_color,
            }
            for p in products
        ],
    }


@app.get("/products/{product_id}")
async def products_get(product_id: str):
    """Get a product with all its actions."""
    product = product_catalog.get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail=f"Product not found: {product_id}")
    return product.model_dump(mode="json")


class ProductActionsRequest(BaseModel):
    product_ids: list[str]


@app.post("/products/actions")
async def products_actions(request: ProductActionsRequest):
    """Get actions for a list of products (used by LLM and Designer)."""
    return product_catalog.get_actions_for_products(request.product_ids)


# ============================================================================
# Blue Team Integration Endpoints
# ============================================================================

@app.get("/integrations/status")
async def integrations_status():
    """Check connectivity status of all Blue Team tool integrations."""
    statuses = await integration_client.check_status()
    return {
        "integrations": [s.to_dict() for s in statuses],
        "connected_count": sum(1 for s in statuses if s.connected),
        "total_count": len(statuses),
    }


@app.get("/integrations/threats")
async def integrations_threats(limit: int = 10):
    """Fetch recent threats from Blue-Team-News integration."""
    threats = await integration_client.get_recent_threats(limit=limit)
    return {
        "threats": [t.to_dict() for t in threats],
        "count": len(threats),
        "source": "Blue-Team-News",
    }


class ThreatContextRequest(BaseModel):
    indicator: str


@app.post("/integrations/context")
async def integrations_context(request: ThreatContextRequest):
    """Get enriched threat context for an IOC from Blue-Team-Assistant."""
    context = await integration_client.get_threat_context(request.indicator)
    return {
        "indicator": request.indicator,
        "context": context,
        "source": "Blue-Team-Assistant",
    }


@app.get("/integrations/playbook-suggestions")
async def integrations_suggestions(cve: str):
    """Get playbook suggestions for a CVE from Blue-Team-Assistant."""
    suggestions = await integration_client.suggest_playbooks(cve)
    return {
        "cve": cve,
        "suggestions": suggestions,
        "source": "Blue-Team-Assistant",
    }


# ============================================================================
# PDF Generation Endpoints
# ============================================================================

class PdfRequest(BaseModel):
    playbook: dict[str, Any]
    include_validation: bool = True


@app.post("/playbook/pdf")
async def generate_pdf(request: PdfRequest):
    """Generate a formatted PDF report from a CACAO playbook."""
    # Guard: limit playbook size to prevent OOM
    workflow = request.playbook.get("workflow", {})
    if len(workflow) > 500:
        raise HTTPException(
            status_code=400,
            detail=f"Playbook has {len(workflow)} steps, maximum is 500 for PDF generation.",
        )

    validation_result = None
    if request.include_validation:
        try:
            playbook = CacaoPlaybook(**request.playbook)
            validator = CacaoValidator()
            result = validator.validate(playbook)
            validation_result = result.to_dict()
        except (ValueError, KeyError, TypeError) as e:
            logger.warning("PDF validation step failed (non-critical): %s", e)

    try:
        pdf_bytes = await asyncio.to_thread(
            pdf_generator.generate, request.playbook, validation_result
        )
    except Exception as e:
        logger.error("PDF generation failed: %s", e)
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

    name = request.playbook.get("name", "playbook").replace(" ", "_")
    filename = f"{name}_report.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.post("/library/{playbook_id}/pdf")
async def generate_library_pdf(playbook_id: str):
    """Generate a PDF report for a playbook from the library."""
    entry = playbook_library.get(playbook_id)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Playbook not found: {playbook_id}")

    playbook_dict = entry.cacao_playbook

    # Guard: limit playbook size
    workflow = playbook_dict.get("workflow", {})
    if len(workflow) > 500:
        raise HTTPException(
            status_code=400,
            detail=f"Playbook has {len(workflow)} steps, maximum is 500 for PDF generation.",
        )

    # Validate
    validation_result = None
    try:
        playbook = CacaoPlaybook(**playbook_dict)
        validator = CacaoValidator()
        result = validator.validate(playbook)
        validation_result = result.to_dict()
    except (ValueError, KeyError, TypeError) as e:
        logger.warning("Library PDF validation step failed (non-critical): %s", e)

    try:
        pdf_bytes = await asyncio.to_thread(
            pdf_generator.generate, playbook_dict, validation_result
        )
    except Exception as e:
        logger.error("Library PDF generation failed: %s", e)
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

    name = playbook_dict.get("name", playbook_id).replace(" ", "_")
    filename = f"{name}_report.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ============================================================================
# File Upload Endpoints
# ============================================================================

@app.post("/files/upload")
async def upload_file(
    file: UploadFile = File(...),
    description: str = Form(""),
    playbook_id: str = Form(""),
    tags: str = Form(""),
):
    """Upload a document (PDF, etc.) to the file storage."""
    content = await file.read()
    max_size = 20 * 1024 * 1024  # 20 MB
    if len(content) > max_size:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 20 MB.")

    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []

    meta = file_storage.save_file(
        content=content,
        original_filename=file.filename or "uploaded_file",
        content_type=file.content_type or "application/octet-stream",
        description=description,
        playbook_id=playbook_id or None,
        tags=tag_list,
    )

    return {"success": True, "file": meta.to_dict()}


@app.get("/files")
async def list_files(playbook_id: Optional[str] = None):
    """List uploaded files, optionally filtered by playbook_id."""
    files = file_storage.list_files(playbook_id=playbook_id)
    return {
        "total": len(files),
        "files": [f.to_dict() for f in files],
    }


@app.get("/files/{file_id}/download")
async def download_file(file_id: str):
    """Download an uploaded file."""
    result = await asyncio.to_thread(file_storage.get_file, file_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"File not found: {file_id}")

    meta, content = result
    return Response(
        content=content,
        media_type=meta.content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{meta.original_filename}"',
        },
    )


@app.delete("/files/{file_id}")
async def delete_file(file_id: str):
    """Delete an uploaded file."""
    deleted = file_storage.delete_file(file_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"File not found: {file_id}")
    return {"success": True, "deleted": file_id}


# ============================================================================
# Resources / Best Practices Endpoints
# ============================================================================

@app.get("/resources/best-practices")
async def resources_best_practices(
    category: Optional[str] = None,
    difficulty: Optional[str] = None,
):
    """List best practices, optionally filtered by category/difficulty."""
    bps = resource_catalog.list_best_practices(category=category, difficulty=difficulty)
    return {
        "total": len(bps),
        "best_practices": [bp.to_summary() for bp in bps],
    }


@app.get("/resources/best-practices/{bp_id}")
async def resources_best_practice_detail(bp_id: str):
    """Get a specific best practice with full steps."""
    bp = resource_catalog.get_best_practice(bp_id)
    if not bp:
        raise HTTPException(status_code=404, detail=f"Best practice not found: {bp_id}")
    return bp.to_dict()


@app.get("/resources/integration-guides")
async def resources_integration_guides(
    category: Optional[str] = None,
    product_id: Optional[str] = None,
):
    """List integration guides, optionally filtered."""
    guides = resource_catalog.list_guides(category=category, product_id=product_id)
    return {
        "total": len(guides),
        "integration_guides": [g.to_summary() for g in guides],
    }


@app.get("/resources/integration-guides/{guide_id}")
async def resources_integration_guide_detail(guide_id: str):
    """Get a specific integration guide with full steps."""
    guide = resource_catalog.get_guide(guide_id)
    if not guide:
        raise HTTPException(status_code=404, detail=f"Integration guide not found: {guide_id}")
    return guide.to_dict()


@app.get("/resources/search")
async def resources_search(q: str = ""):
    """Search across best practices and integration guides."""
    if not q:
        return {"total": 0, "results": []}
    results = resource_catalog.search(q)
    return {"total": len(results), "results": results}


@app.get("/resources/edr")
async def resources_edr():
    """Get EDR-specific resources (best practices + integration guides)."""
    return resource_catalog.get_edr_resources()


# ============================================================================
# Community Repos Endpoints
# ============================================================================

@app.get("/repos")
async def repos_list():
    """List all community playbook repos with their sync status."""
    repos = repo_manager.list_repos()
    return {"total": len(repos), "repos": repos}


@app.get("/repos/status")
async def repos_sync_status():
    """Get overall sync status."""
    return repo_manager.get_sync_status()


@app.post("/repos/sync")
async def repos_sync_all():
    """Trigger sync of all enabled repos (background)."""
    return repo_manager.sync_all(background=True)


@app.post("/repos/{repo_id}/sync")
async def repos_sync_one(repo_id: str):
    """Trigger sync of a single repo."""
    return repo_manager.sync_repo(repo_id)


@app.get("/repos/{repo_id}")
async def repos_get_one(repo_id: str):
    """Get details for a single repo."""
    info = repo_manager.get_repo(repo_id)
    if not info:
        raise HTTPException(status_code=404, detail=f"Repo not found: {repo_id}")
    return info


class RepoToggleRequest(BaseModel):
    enabled: bool


@app.patch("/repos/{repo_id}")
async def repos_toggle(repo_id: str, req: RepoToggleRequest):
    """Enable or disable a repo."""
    return repo_manager.toggle_repo(repo_id, req.enabled)
