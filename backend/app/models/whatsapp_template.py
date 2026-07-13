"""Meta-synced WhatsApp Business template (Phase 1/2).

Distinct from ``Template`` (app/models/template.py, the generic email/sms/
whatsapp/push template CRUD used by the frontend template editor): that
model's shape (name/subject/content) doesn't fit Meta's actual WhatsApp
template structure (named header/body/footer/buttons components, a
provider-assigned id, a language + Meta-controlled approval status). The
only writers are WhatsAppTemplateService.create_draft() (local DRAFT rows,
Phase 2), .submit_to_meta() (sets provider_template_id/status on genuine
Meta acceptance, Phase 3), and .sync_from_meta() (mirrors Meta's state,
Phase 4) — there is still no direct create/update/delete API; "editing" a
template always produces a new version row (see family_id/version below),
never an in-place overwrite of an already-submitted row.

Versioning (Phase 5): each edit-and-resubmit creates a NEW row rather than
mutating the prior one, so multiple rows can legitimately share
(template_name, language) — the old hard UNIQUE(template_name, language)
constraint was dropped for this reason (see migration
a6b7c8d9e0f1_whatsapp_template_versioning.py). ``family_id`` groups every
version of one logical template together (a brand-new template's first
version has family_id == its own id); ``version`` is a per-family,
monotonically increasing counter starting at 1. "Latest approved" always
means: within one family_id, the highest-``version`` row whose status is
APPROVED — never simply the highest-version row overall (a newer
Pending/Rejected resubmission must not shadow a still-live older Approved
version).
"""

from sqlalchemy import Column, DateTime, Integer, String, Text, JSON, Index
from sqlalchemy.dialects.postgresql import UUID

from .base import Base, BaseModel


class WhatsAppTemplate(Base, BaseModel):
    __tablename__ = "whatsapp_templates"

    # Meta's own template id — the dedupe key sync_from_meta() upserts on
    # ("Do not duplicate existing templates"). NULL for a DRAFT row that has
    # never been submitted to Meta yet (Phase 2) — see the CHECK-free
    # nullable column and the sync-time uniqueness handled at the
    # application level in get_by_provider_template_id().
    provider_template_id = Column(String(255), nullable=True, unique=True, index=True)
    # Meta's template "name" — what a send actually addresses the template
    # by (Graph API template sends take name + language, not an internal id).
    template_name = Column(String(255), nullable=False, index=True)
    language = Column(String(20), nullable=False)
    category = Column(String(50), nullable=True)
    # Meta's own approval status string (APPROVED/PENDING/REJECTED/PAUSED/
    # DISABLED) plus JawCom's own pre-submission "DRAFT" (Phase 2) — not
    # JawCom's generic TemplateStatus enum, deliberately not reused since
    # it's a different, mostly Meta-controlled state machine.
    status = Column(String(20), nullable=False, index=True)
    header_type = Column(String(20), nullable=True)  # TEXT/IMAGE/VIDEO/DOCUMENT/None
    # Populated only when header_type == "TEXT" (Meta headers carry either
    # static text or a media handle, never both).
    header_text = Column(Text, nullable=True)
    # Stub for a future media header upload flow (Phase 2 — "build the
    # field/schema now... do not fully build media handling"). Holds a
    # source URL/reference only; there is no upload endpoint yet, and Meta
    # actually requires a pre-uploaded media *handle* (not a bare URL) at
    # submission time — submit_to_meta() does not yet support HEADER
    # components with header_type != TEXT, and raises clearly if attempted
    # rather than silently sending something Meta will reject.
    header_media_url = Column(Text, nullable=True)
    body = Column(Text, nullable=False)
    footer = Column(Text, nullable=True)
    buttons = Column(JSON, nullable=True)  # Meta's BUTTONS component, verbatim
    # Positional variable placeholders found in body (Meta templates use
    # {{1}}, {{2}}, ... — a different convention from JawCom's own Jinja2
    # {{name}} templates, see app/templates/renderer.py). Extracted at
    # sync/create time, not re-derived at send/preview time.
    variables = Column(JSON, nullable=True)
    # Per-variable example values (positional list, e.g. ["John", "Acme"]) —
    # Meta requires these at submission time for any BODY with variables
    # (Phase 2's "Example values ... required by Meta for submission").
    examples = Column(JSON, nullable=True)

    # Versioning (Phase 5) — see module docstring.
    family_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    version = Column(Integer, nullable=False, default=1)

    # Phase 4/7 — mirrored from Meta on sync, operator-visible.
    quality_rating = Column(String(20), nullable=True)  # Meta's GREEN/YELLOW/RED/UNKNOWN
    rejection_reason = Column(Text, nullable=True)
    # Per-row freshness marker — set by both sync_from_meta() (every scanned
    # row, including ones with no field changes) and the message_template_
    # status_update webhook handler (app/api/meta_webhook_routes.py), so a
    # row's own "last confirmed against Meta" time is visible even when only
    # one row changed rather than a full sync. Distinct from the global,
    # sync-run-level timestamp in email_sync_state (get_last_synced_at()).
    last_synced_at = Column(DateTime, nullable=True)

    # Phase 7 — incremented by MetaWhatsAppIntegration.execute() on every
    # confirmed (non-failed) Meta send that used this exact row, covering
    # both Manual Send and Journey/Automation without touching Execution
    # Engine (see app/integrations/native_providers.py).
    usage_count = Column(Integer, nullable=False, default=0)
    last_used_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("ix_whatsapp_templates_family_status", "family_id", "status"),
        Index("ix_whatsapp_templates_name_lang_status", "template_name", "language", "status"),
    )
