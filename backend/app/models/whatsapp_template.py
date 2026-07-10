"""Meta-synced WhatsApp Business template (Phase 1, Feature 1/2).

Distinct from ``Template`` (app/models/template.py, the generic email/sms/
whatsapp/push template CRUD used by the frontend template editor): that
model's shape (name/subject/content) doesn't fit Meta's actual WhatsApp
template structure (named header/body/footer/buttons components, a
provider-assigned id, a language + Meta-controlled approval status). Rows
here are never manually created — the only writer is
WhatsAppTemplateService.sync_from_meta() (Feature 2/8); there is
deliberately no create/update/delete API for this table, since JAWCOM's
"single source of truth" for WhatsApp templates is Meta's approved template
catalog, mirrored here, not a manually authored duplicate of it.
"""

from sqlalchemy import Column, String, Text, JSON, Index

from .base import Base, BaseModel


class WhatsAppTemplate(Base, BaseModel):
    __tablename__ = "whatsapp_templates"

    # Meta's own template id — the dedupe key sync_from_meta() upserts on
    # ("Do not duplicate existing templates", Feature 2).
    provider_template_id = Column(String(255), nullable=False, unique=True, index=True)
    # Meta's template "name" — what a send actually addresses the template
    # by (Graph API template sends take name + language, not an internal id).
    template_name = Column(String(255), nullable=False, index=True)
    language = Column(String(20), nullable=False)
    category = Column(String(50), nullable=True)
    # Meta's own approval status string (APPROVED/PENDING/REJECTED/PAUSED/
    # DISABLED) — not JawCom's TemplateStatus enum, deliberately not reused
    # since it's a different, Meta-controlled state machine.
    status = Column(String(20), nullable=False, index=True)
    header_type = Column(String(20), nullable=True)  # TEXT/IMAGE/VIDEO/DOCUMENT/None
    body = Column(Text, nullable=False)
    footer = Column(Text, nullable=True)
    buttons = Column(JSON, nullable=True)  # Meta's BUTTONS component, verbatim
    # Positional variable placeholders found in body (Meta templates use
    # {{1}}, {{2}}, ... — a different convention from JawCom's own Jinja2
    # {{name}} templates, see app/templates/renderer.py). Extracted at sync
    # time by WhatsAppTemplateService, not re-derived at send/preview time.
    variables = Column(JSON, nullable=True)

    __table_args__ = (
        # A send resolves a template by (name, language) — this is the
        # actual lookup key Feature 5 uses, so it must be unique too (Meta
        # itself enforces this per WABA).
        Index(
            "uq_whatsapp_templates_name_language",
            "template_name", "language",
            unique=True,
        ),
    )
