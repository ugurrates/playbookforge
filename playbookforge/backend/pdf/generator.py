"""
PlaybookForge — PDF Report Generator.

Generates formatted, readable PDF reports from CACAO v2.0 playbooks
using ReportLab Platypus for professional layout.
"""

from __future__ import annotations

import io
from datetime import datetime
from typing import Any, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm, cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    HRFlowable,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


# ============================================================================
# Color Theme (dark-mode inspired)
# ============================================================================

BRAND_COLOR = colors.HexColor("#6366f1")  # indigo-500
HEADER_BG = colors.HexColor("#1e293b")  # slate-800
ROW_ALT_BG = colors.HexColor("#f1f5f9")  # slate-100
ERROR_COLOR = colors.HexColor("#ef4444")
WARNING_COLOR = colors.HexColor("#f59e0b")
INFO_COLOR = colors.HexColor("#3b82f6")
SUCCESS_COLOR = colors.HexColor("#22c55e")

STEP_TYPE_COLORS = {
    "start": colors.HexColor("#6b7280"),
    "end": colors.HexColor("#6b7280"),
    "action": colors.HexColor("#3b82f6"),
    "playbook-action": colors.HexColor("#8b5cf6"),
    "if-condition": colors.HexColor("#eab308"),
    "while-condition": colors.HexColor("#ca8a04"),
    "switch-condition": colors.HexColor("#ca8a04"),
    "parallel": colors.HexColor("#22c55e"),
}


# ============================================================================
# Custom Styles
# ============================================================================

def _build_styles():
    """Build custom paragraph styles for the PDF."""
    base = getSampleStyleSheet()

    styles = {
        "title": ParagraphStyle(
            "PFTitle",
            parent=base["Title"],
            fontSize=24,
            leading=30,
            textColor=BRAND_COLOR,
            spaceAfter=6 * mm,
        ),
        "subtitle": ParagraphStyle(
            "PFSubtitle",
            parent=base["Normal"],
            fontSize=12,
            leading=16,
            textColor=colors.HexColor("#64748b"),
            spaceAfter=10 * mm,
        ),
        "heading1": ParagraphStyle(
            "PFH1",
            parent=base["Heading1"],
            fontSize=16,
            leading=22,
            textColor=HEADER_BG,
            spaceBefore=8 * mm,
            spaceAfter=4 * mm,
        ),
        "heading2": ParagraphStyle(
            "PFH2",
            parent=base["Heading2"],
            fontSize=13,
            leading=18,
            textColor=colors.HexColor("#334155"),
            spaceBefore=6 * mm,
            spaceAfter=3 * mm,
        ),
        "body": ParagraphStyle(
            "PFBody",
            parent=base["Normal"],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#1e293b"),
        ),
        "small": ParagraphStyle(
            "PFSmall",
            parent=base["Normal"],
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#64748b"),
        ),
        "code": ParagraphStyle(
            "PFCode",
            parent=base["Normal"],
            fontName="Courier",
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#1e293b"),
            backColor=colors.HexColor("#f8fafc"),
            borderPadding=4,
        ),
        "step_title": ParagraphStyle(
            "PFStepTitle",
            parent=base["Normal"],
            fontSize=11,
            leading=15,
            textColor=BRAND_COLOR,
            fontName="Helvetica-Bold",
        ),
        "footer": ParagraphStyle(
            "PFFooter",
            parent=base["Normal"],
            fontSize=7,
            leading=10,
            textColor=colors.HexColor("#94a3b8"),
            alignment=TA_CENTER,
        ),
    }
    return styles


# ============================================================================
# Table Helpers
# ============================================================================

TABLE_STYLE = TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTSIZE", (0, 0), (-1, 0), 9),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTSIZE", (0, 1), (-1, -1), 8),
    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ROW_ALT_BG]),
    ("TOPPADDING", (0, 0), (-1, -1), 4),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
])


def _safe(text: Any, max_len: int = 200) -> str:
    """Safely convert to string and truncate for table cells."""
    s = str(text) if text else ""
    # Escape XML special chars for Paragraph
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    if len(s) > max_len:
        s = s[:max_len] + "..."
    return s


# ============================================================================
# PDF Generator
# ============================================================================

class PlaybookPDFGenerator:
    """Generate formatted PDF reports from CACAO playbooks."""

    def __init__(self) -> None:
        self.styles = _build_styles()

    def generate(
        self,
        playbook: dict[str, Any],
        validation_result: Optional[dict[str, Any]] = None,
    ) -> bytes:
        """Generate a PDF report from a CACAO playbook dict.

        Returns the PDF as bytes.
        """
        buf = io.BytesIO()
        doc = SimpleDocTemplate(
            buf,
            pagesize=A4,
            topMargin=15 * mm,
            bottomMargin=20 * mm,
            leftMargin=15 * mm,
            rightMargin=15 * mm,
        )

        story: list = []
        self._add_title_page(story, playbook)
        self._add_summary(story, playbook)
        self._add_workflow(story, playbook)
        self._add_variables(story, playbook)

        if validation_result:
            self._add_validation(story, validation_result)

        # Footer
        story.append(Spacer(1, 10 * mm))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e2e8f0")))
        story.append(Spacer(1, 3 * mm))
        ts = datetime.now(tz=__import__('datetime').timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        story.append(Paragraph(
            f"Generated by PlaybookForge | CACAO v2.0 Standard | {ts}",
            self.styles["footer"],
        ))

        doc.build(story)
        return buf.getvalue()

    # ------------------------------------------------------------------
    # Title Page
    # ------------------------------------------------------------------

    def _add_title_page(self, story: list, pb: dict) -> None:
        story.append(Spacer(1, 20 * mm))
        story.append(Paragraph("PlaybookForge", self.styles["subtitle"]))
        story.append(Paragraph(
            _safe(pb.get("name", "Untitled Playbook"), 200),
            self.styles["title"],
        ))

        desc = pb.get("description", "")
        if desc:
            story.append(Paragraph(_safe(desc, 500), self.styles["body"]))
            story.append(Spacer(1, 6 * mm))

        # Metadata table
        meta_data = [
            ["Field", "Value"],
            ["Playbook ID", _safe(pb.get("id", "N/A"), 80)],
            ["Spec Version", _safe(pb.get("spec_version", "2.0"))],
            ["Created", _safe(pb.get("created", "N/A"))],
            ["Modified", _safe(pb.get("modified", "N/A"))],
        ]

        ptypes = pb.get("playbook_types", [])
        if ptypes:
            meta_data.append(["Playbook Types", ", ".join(str(t) for t in ptypes)])

        labels = pb.get("labels", [])
        if labels:
            meta_data.append(["Labels", ", ".join(str(l) for l in labels)])

        if pb.get("priority"):
            meta_data.append(["Priority", str(pb["priority"])])
        if pb.get("severity"):
            meta_data.append(["Severity", str(pb["severity"])])

        # Convert to Paragraph objects for wrapping
        para_data = []
        for row in meta_data:
            para_data.append([
                Paragraph(row[0], self.styles["small"]),
                Paragraph(row[1], self.styles["small"]),
            ])

        col_widths = [35 * mm, 130 * mm]
        tbl = Table(para_data, colWidths=col_widths)
        tbl.setStyle(TABLE_STYLE)
        story.append(tbl)

        story.append(PageBreak())

    # ------------------------------------------------------------------
    # Summary Section
    # ------------------------------------------------------------------

    def _add_summary(self, story: list, pb: dict) -> None:
        story.append(Paragraph("Playbook Summary", self.styles["heading1"]))
        story.append(HRFlowable(width="100%", thickness=1, color=BRAND_COLOR))
        story.append(Spacer(1, 4 * mm))

        workflow = pb.get("workflow", {})
        variables = pb.get("playbook_variables", {})
        ext_refs = pb.get("external_references", [])

        # Count step types
        type_counts: dict[str, int] = {}
        for step in workflow.values():
            st = step.get("type", "unknown") if isinstance(step, dict) else "unknown"
            type_counts[st] = type_counts.get(st, 0) + 1

        summary_data = [
            ["Metric", "Value"],
            ["Total Steps", str(len(workflow))],
        ]
        for stype, count in sorted(type_counts.items()):
            summary_data.append([f"  {stype} steps", str(count)])

        summary_data.append(["Variables", str(len(variables))])
        summary_data.append(["External References", str(len(ext_refs))])

        # MITRE techniques
        mitre = []
        for ref in ext_refs:
            if isinstance(ref, dict):
                name = ref.get("name", "")
                if name.startswith("T") and len(name) > 1:
                    mitre.append(name)
        if mitre:
            summary_data.append(["MITRE Techniques", ", ".join(mitre)])

        para_data = []
        for row in summary_data:
            para_data.append([
                Paragraph(row[0], self.styles["small"]),
                Paragraph(row[1], self.styles["small"]),
            ])

        col_widths = [50 * mm, 115 * mm]
        tbl = Table(para_data, colWidths=col_widths)
        tbl.setStyle(TABLE_STYLE)
        story.append(tbl)

    # ------------------------------------------------------------------
    # Workflow Steps
    # ------------------------------------------------------------------

    def _add_workflow(self, story: list, pb: dict) -> None:
        story.append(Paragraph("Workflow Steps", self.styles["heading1"]))
        story.append(HRFlowable(width="100%", thickness=1, color=BRAND_COLOR))
        story.append(Spacer(1, 4 * mm))

        workflow = pb.get("workflow", {})
        start_id = pb.get("workflow_start", "")

        # Order steps: start first, then follow on_completion chain, then remaining
        ordered_ids = self._order_steps(workflow, start_id)

        for i, step_id in enumerate(ordered_ids, 1):
            step = workflow.get(step_id, {})
            if not isinstance(step, dict):
                continue

            stype = step.get("type", "unknown")
            sname = step.get("name", step_id.split("--")[-1][:20])

            story.append(Paragraph(
                f"Step {i}: {_safe(sname)} <font color='#94a3b8'>[{stype}]</font>",
                self.styles["step_title"],
            ))

            desc = step.get("description", "")
            if desc:
                story.append(Paragraph(_safe(desc, 400), self.styles["body"]))

            # Step detail table
            detail_rows = [["Property", "Value"]]

            detail_rows.append(["Step ID", _safe(step_id, 60)])

            if step.get("on_completion"):
                detail_rows.append(["Next Step", _safe(step["on_completion"], 60)])
            if step.get("on_success"):
                detail_rows.append(["On Success", _safe(step["on_success"], 60)])
            if step.get("on_failure"):
                detail_rows.append(["On Failure", _safe(step["on_failure"], 60)])
            if step.get("on_true"):
                detail_rows.append(["On True", _safe(step["on_true"], 60)])
            if step.get("on_false"):
                detail_rows.append(["On False", _safe(step["on_false"], 60)])
            if step.get("condition"):
                detail_rows.append(["Condition", _safe(step["condition"], 200)])
            if step.get("next_steps"):
                detail_rows.append(["Parallel Branches", ", ".join(
                    _safe(s, 40) for s in step["next_steps"]
                )])

            # Commands
            commands = step.get("commands", [])
            if commands:
                for ci, cmd in enumerate(commands):
                    if isinstance(cmd, dict):
                        cmd_text = cmd.get("command", cmd.get("description", ""))
                        cmd_type = cmd.get("type", "manual")
                        detail_rows.append([
                            f"Command {ci + 1} ({cmd_type})",
                            _safe(cmd_text, 200),
                        ])

            if len(detail_rows) > 1:
                para_detail = []
                for row in detail_rows:
                    para_detail.append([
                        Paragraph(row[0], self.styles["small"]),
                        Paragraph(row[1], self.styles["small"]),
                    ])

                col_widths = [40 * mm, 125 * mm]
                tbl = Table(para_detail, colWidths=col_widths)
                tbl.setStyle(TABLE_STYLE)
                story.append(Spacer(1, 2 * mm))
                story.append(tbl)

            story.append(Spacer(1, 4 * mm))

    def _order_steps(self, workflow: dict, start_id: str) -> list[str]:
        """Order steps: start first, follow chain, then remaining."""
        ordered: list[str] = []
        visited: set[str] = set()

        def _walk(sid: str) -> None:
            if sid in visited or sid not in workflow:
                return
            visited.add(sid)
            ordered.append(sid)
            step = workflow[sid]
            if isinstance(step, dict):
                for key in ("on_completion", "on_success", "on_failure", "on_true", "on_false"):
                    nxt = step.get(key)
                    if nxt:
                        _walk(nxt)
                for ns in step.get("next_steps", []):
                    _walk(ns)

        if start_id:
            _walk(start_id)

        # Add remaining steps not reachable from start
        for sid in workflow:
            if sid not in visited:
                ordered.append(sid)

        return ordered

    # ------------------------------------------------------------------
    # Variables
    # ------------------------------------------------------------------

    def _add_variables(self, story: list, pb: dict) -> None:
        variables = pb.get("playbook_variables", {})
        if not variables:
            return

        story.append(Paragraph("Playbook Variables", self.styles["heading1"]))
        story.append(HRFlowable(width="100%", thickness=1, color=BRAND_COLOR))
        story.append(Spacer(1, 4 * mm))

        var_data = [["Name", "Type", "Value", "Description"]]
        for vname, vdef in variables.items():
            if isinstance(vdef, dict):
                var_data.append([
                    _safe(vname, 40),
                    _safe(vdef.get("type", "string"), 20),
                    _safe(vdef.get("value", ""), 60),
                    _safe(vdef.get("description", ""), 80),
                ])

        if len(var_data) > 1:
            para_data = []
            for row in var_data:
                para_data.append([Paragraph(c, self.styles["small"]) for c in row])

            col_widths = [35 * mm, 20 * mm, 50 * mm, 60 * mm]
            tbl = Table(para_data, colWidths=col_widths)
            tbl.setStyle(TABLE_STYLE)
            story.append(tbl)

    # ------------------------------------------------------------------
    # Validation Report
    # ------------------------------------------------------------------

    def _add_validation(self, story: list, result: dict) -> None:
        story.append(Paragraph("Validation Report", self.styles["heading1"]))
        story.append(HRFlowable(width="100%", thickness=1, color=BRAND_COLOR))
        story.append(Spacer(1, 4 * mm))

        is_valid = result.get("valid", False)
        errors = result.get("error_count", 0)
        warnings = result.get("warning_count", 0)

        status_text = f"<font color='{'#22c55e' if is_valid else '#ef4444'}'>{'VALID' if is_valid else 'INVALID'}</font>"
        story.append(Paragraph(
            f"Status: {status_text} &nbsp; | &nbsp; Errors: {errors} &nbsp; | &nbsp; Warnings: {warnings}",
            self.styles["body"],
        ))
        story.append(Spacer(1, 3 * mm))

        issues = result.get("issues", [])
        if issues:
            issue_data = [["Severity", "Code", "Message", "Path"]]
            for issue in issues:
                if isinstance(issue, dict):
                    issue_data.append([
                        _safe(issue.get("severity", "info")),
                        _safe(issue.get("code", "")),
                        _safe(issue.get("message", ""), 120),
                        _safe(issue.get("path", "")),
                    ])

            if len(issue_data) > 1:
                para_data = []
                for row in issue_data:
                    para_data.append([Paragraph(c, self.styles["small"]) for c in row])

                col_widths = [20 * mm, 25 * mm, 85 * mm, 35 * mm]
                tbl = Table(para_data, colWidths=col_widths)
                tbl.setStyle(TABLE_STYLE)
                story.append(tbl)


# Global instance
pdf_generator = PlaybookPDFGenerator()
