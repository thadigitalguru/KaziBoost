from __future__ import annotations

import csv
import hashlib
import io
import os
import re
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from .seo_persistence import SEOPersistence


@dataclass
class Tenant:
    id: str
    name: str


@dataclass
class User:
    id: str
    tenant_id: str
    owner_name: str
    email: str
    role: str
    password_hash: str
    password_salt: str


@dataclass
class TokenSession:
    token: str
    user_id: str
    expires_at: datetime


@dataclass
class Site:
    id: str
    tenant_id: str
    name: str
    template_key: str
    primary_language: str
    status: str
    published_url: str | None = None


@dataclass
class Page:
    id: str
    tenant_id: str
    site_id: str
    slug: str
    title: str
    language: str
    body_blocks: list[str]


@dataclass
class SEOAsset:
    site_id: str
    sitemap_xml: str
    robots_txt: str
    localbusiness_schema: dict


@dataclass
class CRMForm:
    id: str
    tenant_id: str
    name: str
    kind: str
    fields: list[str]


@dataclass
class Contact:
    id: str
    tenant_id: str
    name: str
    phone: str
    email: str
    source: str
    tags: list[str]
    created_at: str
    consent: dict[str, bool]
    anonymized: bool = False


@dataclass
class CRMSegment:
    id: str
    tenant_id: str
    name: str
    tag: str | None
    source: str | None


@dataclass
class CampaignDispatch:
    id: str
    tenant_id: str
    channel: str
    subject: str
    message: str
    tag: str | None
    source: str | None
    recipients: int
    created_at: str


@dataclass
class InteractionEvent:
    id: str
    tenant_id: str
    contact_id: str
    type: str
    source: str
    message: str
    form_id: str
    created_at: str


@dataclass
class WhatsAppConversation:
    thread_id: str
    tenant_id: str
    from_phone: str
    status: str
    last_message: str
    language: str
    assigned_to: str | None
    updated_at: str


@dataclass
class Payment:
    payment_id: str
    tenant_id: str
    provider: str
    phone: str
    amount: int
    currency: str
    reference: str
    status: str
    created_at: str
    contact_id: str | None = None
    provider_tx_id: str | None = None


@dataclass
class WhatsAppReminder:
    id: str
    tenant_id: str
    thread_id: str
    message: str
    status: str
    created_at: str


@dataclass
class AuditEvent:
    id: str
    tenant_id: str
    event_type: str
    actor_user_id: str | None
    entity_type: str
    entity_id: str
    metadata: dict[str, str]
    created_at: str


@dataclass
class PaymentRefund:
    refund_id: str
    tenant_id: str
    payment_id: str
    amount: int
    reason: str
    status: str
    created_at: str


@dataclass
class TrainingArticle:
    id: str
    tenant_id: str
    title: str
    content: str
    category: str
    created_at: str


@dataclass
class ContentCalendarItem:
    id: str
    tenant_id: str
    title: str
    keyword: str
    scheduled_for: str
    language: str
    status: str
    created_at: str


class InMemoryStore:
    ALLOWED_ROLES = {"owner", "manager", "marketer", "support", "viewer"}

    def __init__(self, db_path: str | None = None, token_ttl_minutes: int = 60, login_block_minutes: int = 10) -> None:
        self.tenants: dict[str, Tenant] = {}
        self.users_by_id: dict[str, User] = {}
        self.users_by_email: dict[str, User] = {}
        self.tokens: dict[str, TokenSession] = {}
        self.token_ttl_minutes = token_ttl_minutes
        self.login_block_minutes = login_block_minutes
        self.login_failures: dict[str, dict[str, object]] = {}

        self.sites: dict[str, Site] = {}
        self.pages: dict[str, Page] = {}
        self.pages_by_site: dict[str, list[str]] = {}
        self.seo_assets: dict[str, SEOAsset] = {}

        self.crm_forms: dict[str, CRMForm] = {}
        self.contacts: dict[str, Contact] = {}
        self.contacts_by_tenant: dict[str, list[str]] = {}
        self.crm_segments: dict[str, CRMSegment] = {}
        self.crm_segments_by_tenant: dict[str, list[str]] = {}
        self.campaign_dispatches: dict[str, CampaignDispatch] = {}
        self.campaigns_by_tenant: dict[str, list[str]] = {}
        self.interactions: dict[str, InteractionEvent] = {}
        self.interactions_by_contact: dict[str, list[str]] = {}

        self.keyword_workspaces: dict[str, dict[str, list[str]]] = {}
        self.seo_calendar: dict[str, ContentCalendarItem] = {}
        self.seo_calendar_by_tenant: dict[str, list[str]] = {}
        self.seo_persistence = SEOPersistence(db_path=db_path)

        self.whatsapp_conversations: dict[str, WhatsAppConversation] = {}
        self.whatsapp_by_tenant: dict[str, list[str]] = {}
        self.whatsapp_faq_by_tenant: dict[str, list[dict[str, str]]] = {}
        self.whatsapp_events_by_tenant: dict[str, dict[str, str]] = {}
        self.whatsapp_reminders: dict[str, WhatsAppReminder] = {}
        self.whatsapp_reminders_by_tenant: dict[str, list[str]] = {}

        self.payments: dict[str, Payment] = {}
        self.payment_refunds: dict[str, PaymentRefund] = {}
        self.refunds_by_payment: dict[str, list[str]] = {}
        self.report_schedules: dict[str, list[dict[str, str]]] = {}

        self.training_articles: dict[str, TrainingArticle] = {}
        self.training_by_tenant: dict[str, list[str]] = {}

        self.audit_events: dict[str, AuditEvent] = {}
        self.audit_by_tenant: dict[str, list[str]] = {}

        self.metrics: dict[str, int] = {
            "auth_logins_total": 0,
            "whatsapp_events_total": 0,
            "payments_callbacks_total": 0,
        }

    @staticmethod
    def _hash_password(password: str, salt: str) -> str:
        return hashlib.sha256(f"{salt}:{password}".encode("utf-8")).hexdigest()

    @staticmethod
    def _password_is_strong(password: str) -> bool:
        return bool(
            len(password) >= 10
            and re.search(r"[A-Z]", password)
            and re.search(r"[a-z]", password)
            and re.search(r"\d", password)
            and re.search(r"[^A-Za-z0-9]", password)
        )

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(tz=UTC).isoformat()

    def record_audit_event(
        self,
        tenant_id: str,
        event_type: str,
        entity_type: str,
        entity_id: str,
        actor_user_id: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> AuditEvent:
        event = AuditEvent(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            event_type=event_type,
            actor_user_id=actor_user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            metadata=metadata or {},
            created_at=self._now_iso(),
        )
        self.audit_events[event.id] = event
        self.audit_by_tenant.setdefault(tenant_id, []).append(event.id)
        return event

    def list_audit_events(self, tenant_id: str, limit: int = 100) -> list[AuditEvent]:
        event_ids = self.audit_by_tenant.get(tenant_id, [])[-limit:]
        return [self.audit_events[event_id] for event_id in reversed(event_ids)]

    def create_tenant_and_owner(self, business_name: str, owner_name: str, email: str, password: str) -> tuple[Tenant, User]:
        normalized_email = email.strip().lower()
        if normalized_email in self.users_by_email:
            raise ValueError("Email already exists")
        if not self._password_is_strong(password):
            raise ValueError("Password must include upper/lowercase letters, number, symbol, and be at least 10 chars")

        tenant = Tenant(id=str(uuid.uuid4()), name=business_name)
        salt = secrets.token_hex(8)
        user = User(
            id=str(uuid.uuid4()),
            tenant_id=tenant.id,
            owner_name=owner_name,
            email=normalized_email,
            role="owner",
            password_hash=self._hash_password(password, salt),
            password_salt=salt,
        )
        self.tenants[tenant.id] = tenant
        self.users_by_id[user.id] = user
        self.users_by_email[user.email] = user
        return tenant, user

    def create_teammate(
        self,
        tenant_id: str,
        owner_name: str,
        email: str,
        password: str,
        role: str,
        actor_user_id: str | None = None,
    ) -> User:
        normalized_email = email.strip().lower()
        if normalized_email in self.users_by_email:
            raise ValueError("Email already exists")
        if role not in self.ALLOWED_ROLES or role == "owner":
            raise ValueError("Invalid teammate role")
        if not self._password_is_strong(password):
            raise ValueError("Password must include upper/lowercase letters, number, symbol, and be at least 10 chars")

        salt = secrets.token_hex(8)
        user = User(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            owner_name=owner_name,
            email=normalized_email,
            role=role,
            password_hash=self._hash_password(password, salt),
            password_salt=salt,
        )
        self.users_by_id[user.id] = user
        self.users_by_email[user.email] = user
        self.record_audit_event(
            tenant_id=tenant_id,
            event_type="teammate.created",
            entity_type="user",
            entity_id=user.id,
            actor_user_id=actor_user_id,
            metadata={"role": role},
        )
        return user

    def update_user_role(self, tenant_id: str, user_id: str, role: str, actor_user_id: str | None = None) -> User:
        if role not in self.ALLOWED_ROLES:
            raise ValueError("Invalid role")
        user = self.users_by_id.get(user_id)
        if not user or user.tenant_id != tenant_id:
            raise ValueError("User not found")
        user.role = role
        self.record_audit_event(
            tenant_id=tenant_id,
            event_type="user.role.updated",
            entity_type="user",
            entity_id=user.id,
            actor_user_id=actor_user_id,
            metadata={"role": role},
        )
        return user

    def authenticate(self, email: str, password: str) -> tuple[str, User, Tenant] | None:
        normalized_email = email.strip().lower()
        tracker = self.login_failures.get(normalized_email)
        if tracker and tracker.get("blocked_until") and datetime.now(tz=UTC) < tracker["blocked_until"]:
            raise PermissionError("Too many failed login attempts. Try again later.")

        user = self.users_by_email.get(normalized_email)
        if not user or user.password_hash != self._hash_password(password, user.password_salt):
            failure = self.login_failures.setdefault(normalized_email, {"count": 0, "blocked_until": None})
            failure["count"] = int(failure["count"]) + 1
            if int(failure["count"]) >= 5:
                failure["blocked_until"] = datetime.now(tz=UTC) + timedelta(minutes=self.login_block_minutes)
            return None

        self.login_failures.pop(normalized_email, None)
        self.metrics["auth_logins_total"] += 1
        tenant = self.tenants[user.tenant_id]
        token = secrets.token_urlsafe(24)
        expires_at = datetime.now(tz=UTC) + timedelta(minutes=self.token_ttl_minutes)
        self.tokens[token] = TokenSession(token=token, user_id=user.id, expires_at=expires_at)
        return token, user, tenant

    def resolve_token(self, token: str) -> tuple[User, Tenant] | None:
        session = self.tokens.get(token)
        if not session:
            return None
        if datetime.now(tz=UTC) > session.expires_at:
            raise PermissionError("Token expired")
        user = self.users_by_id[session.user_id]
        tenant = self.tenants[user.tenant_id]
        return user, tenant

    def revoke_token(self, token: str) -> None:
        self.tokens.pop(token, None)

    def force_expire_token_for_test(self, token: str) -> None:
        session = self.tokens.get(token)
        if not session:
            return
        session.expires_at = datetime.now(tz=UTC) - timedelta(seconds=1)

    def create_site(self, tenant_id: str, name: str, template_key: str, primary_language: str) -> Site:
        site = Site(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            name=name,
            template_key=template_key,
            primary_language=primary_language,
            status="draft",
        )
        self.sites[site.id] = site
        self.pages_by_site[site.id] = []
        return site

    def get_site(self, tenant_id: str, site_id: str) -> Site:
        site = self.sites.get(site_id)
        if not site or site.tenant_id != tenant_id:
            raise ValueError("Site not found")
        return site

    def add_page(self, tenant_id: str, site_id: str, slug: str, title: str, language: str, body_blocks: list[str]) -> Page:
        self.get_site(tenant_id, site_id)
        existing_page_ids = self.pages_by_site.get(site_id, [])
        for page_id in existing_page_ids:
            if self.pages[page_id].slug == slug:
                raise ValueError("Page slug already exists")

        page = Page(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            site_id=site_id,
            slug=slug,
            title=title,
            language=language,
            body_blocks=body_blocks,
        )
        self.pages[page.id] = page
        self.pages_by_site.setdefault(site_id, []).append(page.id)
        return page

    def get_page_by_slug(self, tenant_id: str, site_id: str, slug: str) -> Page:
        self.get_site(tenant_id, site_id)
        for page_id in self.pages_by_site.get(site_id, []):
            page = self.pages[page_id]
            if page.slug == slug:
                return page
        raise ValueError("Page not found")

    def _site_pages(self, site_id: str) -> list[Page]:
        return [self.pages[page_id] for page_id in self.pages_by_site.get(site_id, [])]

    def publish_site(self, tenant_id: str, site_id: str) -> Site:
        site = self.get_site(tenant_id, site_id)
        pages = self._site_pages(site_id)
        if not pages:
            raise ValueError("Cannot publish site without pages")

        published_url = f"https://{site.id}.kaziboost.local"
        site.published_url = published_url
        site.status = "published"

        urls_xml = []
        for page in pages:
            path = "/" if page.slug == "home" else f"/{page.slug}"
            urls_xml.append(f"<url><loc>{published_url}{path}</loc></url>")
        sitemap_xml = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<urlset>" + "".join(urls_xml) + "</urlset>"

        robots_txt = f"User-agent: *\nAllow: /\nSitemap: {published_url}/sitemap.xml\n"
        localbusiness_schema = {
            "@context": "https://schema.org",
            "@type": "LocalBusiness",
            "name": site.name,
            "url": published_url,
            "inLanguage": site.primary_language,
        }

        self.seo_assets[site_id] = SEOAsset(
            site_id=site_id,
            sitemap_xml=sitemap_xml,
            robots_txt=robots_txt,
            localbusiness_schema=localbusiness_schema,
        )
        return site

    def get_seo_assets(self, tenant_id: str, site_id: str) -> SEOAsset:
        self.get_site(tenant_id, site_id)
        assets = self.seo_assets.get(site_id)
        if not assets:
            raise ValueError("SEO assets not found")
        return assets

    def hreflang_map(self, tenant_id: str, site_id: str) -> list[dict[str, str]]:
        site = self.get_site(tenant_id, site_id)
        if not site.published_url:
            raise ValueError("Site is not published")
        items: list[dict[str, str]] = []
        for page in self._site_pages(site_id):
            path = "/" if page.slug == "home" else f"/{page.slug}"
            items.append({"language": page.language, "slug": page.slug, "href": f"{site.published_url}{path}"})
        return items

    def create_crm_form(self, tenant_id: str, name: str, kind: str, fields: list[str]) -> CRMForm:
        form = CRMForm(id=str(uuid.uuid4()), tenant_id=tenant_id, name=name, kind=kind, fields=fields)
        self.crm_forms[form.id] = form
        return form

    def _get_form(self, tenant_id: str, form_id: str) -> CRMForm:
        form = self.crm_forms.get(form_id)
        if not form or form.tenant_id != tenant_id:
            raise ValueError("Form not found")
        return form

    def submit_form(
        self,
        tenant_id: str,
        form_id: str,
        name: str,
        phone: str,
        email: str,
        message: str,
        source: str,
        tags: list[str],
    ) -> tuple[InteractionEvent, Contact]:
        self._get_form(tenant_id, form_id)
        normalized_email = email.strip().lower()

        existing_contact = None
        for contact_id in self.contacts_by_tenant.get(tenant_id, []):
            contact = self.contacts[contact_id]
            if contact.email == normalized_email:
                existing_contact = contact
                break

        if existing_contact:
            merged_tags = sorted(set(existing_contact.tags + tags))
            existing_contact.tags = merged_tags
            contact = existing_contact
        else:
            contact = Contact(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                name=name,
                phone=phone,
                email=normalized_email,
                source=source,
                tags=sorted(set(tags)),
                created_at=self._now_iso(),
                consent={"email_marketing": False, "sms_marketing": False},
                anonymized=False,
            )
            self.contacts[contact.id] = contact
            self.contacts_by_tenant.setdefault(tenant_id, []).append(contact.id)

        interaction = InteractionEvent(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            contact_id=contact.id,
            type="form_submission",
            source=source,
            message=message,
            form_id=form_id,
            created_at=self._now_iso(),
        )
        self.interactions[interaction.id] = interaction
        self.interactions_by_contact.setdefault(contact.id, []).append(interaction.id)
        return interaction, contact

    def list_contacts(self, tenant_id: str, source: str | None = None, tag: str | None = None) -> list[Contact]:
        items = [self.contacts[contact_id] for contact_id in self.contacts_by_tenant.get(tenant_id, [])]
        if source:
            items = [contact for contact in items if contact.source == source]
        if tag:
            items = [contact for contact in items if tag in contact.tags]
        return items

    def export_contacts_csv(self, tenant_id: str, source: str | None = None, tag: str | None = None) -> str:
        contacts = self.list_contacts(tenant_id=tenant_id, source=source, tag=tag)
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "name", "phone", "email", "source", "tags", "created_at"])
        for contact in contacts:
            writer.writerow(
                [
                    contact.id,
                    contact.name,
                    contact.phone,
                    contact.email,
                    contact.source,
                    "|".join(contact.tags),
                    contact.created_at,
                ]
            )
        return output.getvalue()

    def create_segment(self, tenant_id: str, name: str, tag: str | None, source: str | None) -> CRMSegment:
        segment = CRMSegment(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            name=name,
            tag=tag,
            source=source,
        )
        self.crm_segments[segment.id] = segment
        self.crm_segments_by_tenant.setdefault(tenant_id, []).append(segment.id)
        return segment

    def get_segment_contacts(self, tenant_id: str, segment_id: str) -> list[Contact]:
        segment = self.crm_segments.get(segment_id)
        if not segment or segment.tenant_id != tenant_id:
            raise ValueError("Segment not found")
        return self.list_contacts(tenant_id=tenant_id, source=segment.source, tag=segment.tag)

    def send_campaign(
        self,
        tenant_id: str,
        channel: str,
        subject: str,
        message: str,
        tag: str | None,
        source: str | None,
    ) -> CampaignDispatch:
        recipients = self.list_contacts(tenant_id=tenant_id, source=source, tag=tag)
        campaign = CampaignDispatch(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            channel=channel,
            subject=subject,
            message=message,
            tag=tag,
            source=source,
            recipients=len(recipients),
            created_at=self._now_iso(),
        )
        self.campaign_dispatches[campaign.id] = campaign
        self.campaigns_by_tenant.setdefault(tenant_id, []).append(campaign.id)
        self.record_audit_event(
            tenant_id=tenant_id,
            event_type="campaign.sent",
            entity_type="campaign",
            entity_id=campaign.id,
            metadata={"channel": channel, "recipients": str(campaign.recipients)},
        )
        return campaign

    def campaign_history(self, tenant_id: str) -> list[CampaignDispatch]:
        ids = self.campaigns_by_tenant.get(tenant_id, [])
        return [self.campaign_dispatches[c_id] for c_id in reversed(ids)]

    def campaign_stats(self, tenant_id: str) -> dict[str, object]:
        items = self.campaign_history(tenant_id=tenant_id)
        by_channel: dict[str, int] = {}
        total_recipients = 0
        for item in items:
            by_channel[item.channel] = by_channel.get(item.channel, 0) + 1
            total_recipients += item.recipients
        return {
            "total_campaigns": len(items),
            "total_recipients": total_recipients,
            "by_channel": by_channel,
        }

    def get_contact(self, tenant_id: str, contact_id: str) -> Contact:
        contact = self.contacts.get(contact_id)
        if not contact or contact.tenant_id != tenant_id:
            raise ValueError("Contact not found")
        return contact

    def get_contact_timeline(self, tenant_id: str, contact_id: str) -> list[InteractionEvent]:
        self.get_contact(tenant_id, contact_id)
        event_ids = self.interactions_by_contact.get(contact_id, [])
        return [self.interactions[event_id] for event_id in event_ids]

    def update_contact_consent(
        self,
        tenant_id: str,
        contact_id: str,
        email_marketing: bool,
        sms_marketing: bool,
        actor_user_id: str | None = None,
    ) -> Contact:
        contact = self.get_contact(tenant_id, contact_id)
        contact.consent = {"email_marketing": email_marketing, "sms_marketing": sms_marketing}
        self.record_audit_event(
            tenant_id=tenant_id,
            event_type="contact.consent.updated",
            entity_type="contact",
            entity_id=contact_id,
            actor_user_id=actor_user_id,
            metadata={"email_marketing": str(email_marketing), "sms_marketing": str(sms_marketing)},
        )
        return contact

    def anonymize_contact(self, tenant_id: str, contact_id: str, actor_user_id: str | None = None) -> Contact:
        contact = self.get_contact(tenant_id, contact_id)
        contact.name = "ANONYMIZED"
        contact.phone = "REDACTED"
        contact.email = f"{contact.id}@redacted.local"
        contact.tags = []
        contact.anonymized = True
        self.record_audit_event(
            tenant_id=tenant_id,
            event_type="contact.anonymized",
            entity_type="contact",
            entity_id=contact_id,
            actor_user_id=actor_user_id,
            metadata={},
        )
        return contact

    def ingest_whatsapp_message(
        self,
        tenant_id: str,
        from_phone: str,
        message_text: str,
        language: str,
        event_id: str,
    ) -> tuple[WhatsAppConversation, bool]:
        processed = self.whatsapp_events_by_tenant.setdefault(tenant_id, {})
        if event_id in processed:
            return self.whatsapp_conversations[processed[event_id]], True

        self.metrics["whatsapp_events_total"] += 1

        existing_thread_id = None
        for thread_id in self.whatsapp_by_tenant.get(tenant_id, []):
            thread = self.whatsapp_conversations[thread_id]
            if thread.from_phone == from_phone:
                existing_thread_id = thread_id
                break

        if existing_thread_id:
            conversation = self.whatsapp_conversations[existing_thread_id]
            conversation.last_message = message_text
            conversation.updated_at = self._now_iso()
            conversation.status = "open"
            processed[event_id] = conversation.thread_id
            return conversation, False

        thread_id = str(uuid.uuid4())
        conversation = WhatsAppConversation(
            thread_id=thread_id,
            tenant_id=tenant_id,
            from_phone=from_phone,
            status="open",
            last_message=message_text,
            language=language,
            assigned_to=None,
            updated_at=self._now_iso(),
        )
        self.whatsapp_conversations[thread_id] = conversation
        self.whatsapp_by_tenant.setdefault(tenant_id, []).append(thread_id)
        processed[event_id] = thread_id
        return conversation, False

    def list_whatsapp_conversations(self, tenant_id: str, status: str | None = None) -> list[WhatsAppConversation]:
        thread_ids = self.whatsapp_by_tenant.get(tenant_id, [])
        items = [self.whatsapp_conversations[thread_id] for thread_id in thread_ids]
        if status:
            items = [item for item in items if item.status == status]
        return items

    def set_whatsapp_status(self, tenant_id: str, thread_id: str, status: str) -> WhatsAppConversation:
        conversation = self.whatsapp_conversations.get(thread_id)
        if not conversation or conversation.tenant_id != tenant_id:
            raise ValueError("Conversation not found")
        conversation.status = status
        conversation.updated_at = self._now_iso()
        return conversation

    def schedule_whatsapp_reminder(self, tenant_id: str, thread_id: str, message: str) -> WhatsAppReminder:
        conversation = self.whatsapp_conversations.get(thread_id)
        if not conversation or conversation.tenant_id != tenant_id:
            raise ValueError("Conversation not found")
        reminder = WhatsAppReminder(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            thread_id=thread_id,
            message=message,
            status="scheduled",
            created_at=self._now_iso(),
        )
        self.whatsapp_reminders[reminder.id] = reminder
        self.whatsapp_reminders_by_tenant.setdefault(tenant_id, []).append(reminder.id)
        self.record_audit_event(
            tenant_id=tenant_id,
            event_type="whatsapp.reminder.scheduled",
            entity_type="whatsapp_reminder",
            entity_id=reminder.id,
            metadata={"thread_id": thread_id},
        )
        return reminder

    def list_whatsapp_reminders(self, tenant_id: str) -> list[WhatsAppReminder]:
        ids = self.whatsapp_reminders_by_tenant.get(tenant_id, [])
        return [self.whatsapp_reminders[item_id] for item_id in reversed(ids)]

    def overdue_whatsapp_queue(self, tenant_id: str) -> list[WhatsAppConversation]:
        items = self.list_whatsapp_conversations(tenant_id=tenant_id, status="open")
        return [item for item in items if item.assigned_to is None]

    def add_whatsapp_faq(self, tenant_id: str, question: str, answer: str) -> dict[str, str]:
        item = {"question": question, "answer": answer}
        self.whatsapp_faq_by_tenant.setdefault(tenant_id, []).append(item)
        return item

    def whatsapp_bot_reply(self, tenant_id: str, thread_id: str) -> dict[str, str]:
        conversation = self.whatsapp_conversations.get(thread_id)
        if not conversation or conversation.tenant_id != tenant_id:
            raise ValueError("Conversation not found")

        message = conversation.last_message.lower()
        faq_items = self.whatsapp_faq_by_tenant.get(tenant_id, [])
        for faq in faq_items:
            question = faq["question"].lower()
            if any(token in question for token in message.split() if len(token) > 3):
                return {"mode": "bot", "reply_text": faq["answer"], "thread_id": thread_id}

        return {
            "mode": "handoff_required",
            "reply_text": "I need a human teammate to help with this request.",
            "thread_id": thread_id,
        }

    def whatsapp_handoff(self, tenant_id: str, thread_id: str, assigned_to: str) -> WhatsAppConversation:
        conversation = self.whatsapp_conversations.get(thread_id)
        if not conversation or conversation.tenant_id != tenant_id:
            raise ValueError("Conversation not found")
        conversation.status = "handoff"
        conversation.assigned_to = assigned_to
        conversation.updated_at = self._now_iso()
        return conversation

    def initiate_mpesa_payment(
        self,
        tenant_id: str,
        phone: str,
        amount: int,
        currency: str,
        reference: str,
        contact_id: str | None = None,
    ) -> Payment:
        payment = Payment(
            payment_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            provider="mpesa",
            phone=phone,
            amount=amount,
            currency=currency,
            reference=reference,
            status="pending",
            created_at=self._now_iso(),
            contact_id=contact_id,
            provider_tx_id=None,
        )
        self.payments[payment.payment_id] = payment
        return payment

    def apply_mpesa_callback(
        self,
        tenant_id: str,
        payment_id: str,
        provider_tx_id: str,
        status: str,
        actor_user_id: str | None = None,
    ) -> dict[str, object]:
        payment = self.get_payment(tenant_id=tenant_id, payment_id=payment_id)
        if payment.provider_tx_id == provider_tx_id:
            return {"payment": payment, "idempotent": True}

        self.metrics["payments_callbacks_total"] += 1

        if payment.status in {"success", "failed"} and status != payment.status:
            raise ValueError("Invalid payment state transition")

        payment.provider_tx_id = provider_tx_id
        payment.status = status
        self.record_audit_event(
            tenant_id=tenant_id,
            event_type="payment.callback.applied",
            entity_type="payment",
            entity_id=payment.payment_id,
            actor_user_id=actor_user_id,
            metadata={"status": status, "provider_tx_id": provider_tx_id},
        )
        return {"payment": payment, "idempotent": False}

    def list_payments_by_contact(self, tenant_id: str, contact_id: str) -> list[Payment]:
        return [
            payment
            for payment in self.payments.values()
            if payment.tenant_id == tenant_id and payment.contact_id == contact_id
        ]

    def get_payment(self, tenant_id: str, payment_id: str) -> Payment:
        payment = self.payments.get(payment_id)
        if not payment or payment.tenant_id != tenant_id:
            raise ValueError("Payment not found")
        return payment

    def create_refund(
        self,
        tenant_id: str,
        payment_id: str,
        amount: int,
        reason: str,
        actor_user_id: str | None = None,
    ) -> PaymentRefund:
        payment = self.get_payment(tenant_id=tenant_id, payment_id=payment_id)
        if payment.status != "success":
            raise ValueError("Only successful payments can be refunded")
        if amount > payment.amount:
            raise ValueError("Refund amount exceeds payment amount")

        refund = PaymentRefund(
            refund_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            payment_id=payment_id,
            amount=amount,
            reason=reason,
            status="refunded",
            created_at=self._now_iso(),
        )
        self.payment_refunds[refund.refund_id] = refund
        self.refunds_by_payment.setdefault(payment_id, []).append(refund.refund_id)
        payment.status = "refunded"
        self.record_audit_event(
            tenant_id=tenant_id,
            event_type="payment.refund.created",
            entity_type="refund",
            entity_id=refund.refund_id,
            actor_user_id=actor_user_id,
            metadata={"payment_id": payment_id, "amount": str(amount)},
        )
        return refund

    def list_refunds(self, tenant_id: str, payment_id: str) -> list[PaymentRefund]:
        self.get_payment(tenant_id=tenant_id, payment_id=payment_id)
        refund_ids = self.refunds_by_payment.get(payment_id, [])
        return [self.payment_refunds[refund_id] for refund_id in refund_ids]

    def payments_summary(self, tenant_id: str) -> dict[str, object]:
        items = [payment for payment in self.payments.values() if payment.tenant_id == tenant_id]
        totals = {"count": len(items), "amount": sum(item.amount for item in items)}
        by_status: dict[str, dict[str, int]] = {}
        for payment in items:
            agg = by_status.setdefault(payment.status, {"count": 0, "amount": 0})
            agg["count"] += 1
            agg["amount"] += payment.amount
        return {"totals": totals, "by_status": by_status}

    def suggest_keywords(self, seed_query: str, location: str, language: str) -> list[dict[str, str]]:
        seed = seed_query.strip().lower()
        loc = location.strip()

        patterns = [
            (f"best {seed} {loc}", "transactional", "high"),
            (f"affordable {seed} {loc}", "transactional", "medium"),
            (f"{seed} near me {loc}", "transactional", "high"),
            (f"top-rated {seed} {loc}", "transactional", "medium"),
            (f"{seed} open now {loc}", "navigational", "medium"),
            (f"trusted {seed} {loc}", "transactional", "low"),
            (f"{seed} services in {loc}", "informational", "medium"),
            (f"how much is {seed} in {loc}", "informational", "medium"),
            (f"{seed} price in {loc}", "informational", "high"),
            (f"{seed} offers {loc}", "transactional", "low"),
            (f"{seed} recommendations {loc}", "informational", "low"),
            (f"fast {seed} {loc}", "transactional", "low"),
            (f"reliable {seed} {loc}", "transactional", "low"),
            (f"{seed} contacts {loc}", "navigational", "medium"),
            (f"{seed} reviews {loc}", "informational", "medium"),
            (f"{seed} deals {loc}", "transactional", "low"),
            (f"{seed} same day {loc}", "transactional", "low"),
            (f"{seed} experts {loc}", "informational", "low"),
            (f"book {seed} {loc}", "transactional", "medium"),
            (f"{seed} whatsapp {loc}", "navigational", "medium"),
            (f"{seed} mpesa payment {loc}", "transactional", "low"),
            (f"{seed} swahili huduma {loc}", "informational", "low"),
        ]

        items = [
            {"keyword": keyword, "intent": intent, "volume_band": volume}
            for keyword, intent, volume in patterns
        ]

        if language == "sw":
            items.append({"keyword": f"{seed} bora {loc}", "intent": "transactional", "volume_band": "medium"})
            items.append({"keyword": f"huduma ya {seed} {loc}", "intent": "informational", "volume_band": "low"})

        return items

    def save_keywords(self, tenant_id: str, workspace: str, keywords: list[str]) -> dict[str, object]:
        persisted = self.seo_persistence.save_keywords(tenant_id=tenant_id, workspace=workspace, keywords=keywords)
        tenant_workspaces = self.keyword_workspaces.setdefault(tenant_id, {})
        tenant_workspaces[workspace] = persisted
        return {"workspace": workspace, "count": len(persisted), "keywords": persisted}

    def get_saved_keywords(self, tenant_id: str, workspace: str) -> dict[str, object]:
        keywords = self.seo_persistence.get_keywords(tenant_id=tenant_id, workspace=workspace)
        tenant_workspaces = self.keyword_workspaces.setdefault(tenant_id, {})
        tenant_workspaces[workspace] = keywords
        return {"workspace": workspace, "count": len(keywords), "keywords": keywords}

    def generate_content(
        self,
        tenant_id: str,
        keyword: str,
        content_type: str,
        tone: str,
        language: str,
        length: str,
    ) -> dict[str, object]:
        keyword_clean = keyword.strip()
        related_terms = [f"{keyword_clean} price", f"{keyword_clean} near me", f"{keyword_clean} tips"]

        if language == "sw":
            title = f"Mwongozo wa {keyword_clean} kwa Biashara za Kenya"
            body = (
                f"Karibu kwenye mwongozo wetu wa {keyword_clean}. "
                f"Makala hii inaelezea mbinu za vitendo za kuboresha mwonekano wa biashara yako mtandaoni, "
                f"kupata leads zaidi, na kuongeza mauzo kwa kutumia SEO ya ndani. "
                f"Mtindo: {tone}. Urefu: {length}. Aina: {content_type}."
            )
            meta_title = f"{keyword_clean} | KaziBoost Kenya"
            meta_description = f"Jifunze jinsi ya kutumia {keyword_clean} kuongeza leads na mauzo kwa biashara yako Kenya."
        else:
            title = f"{keyword_clean}: Practical Growth Guide for Kenyan SMEs"
            body = (
                f"This guide explains how to use {keyword_clean} to improve local search visibility, "
                f"attract qualified leads, and convert more customers through mobile-first journeys. "
                f"Tone: {tone}. Length: {length}. Type: {content_type}."
            )
            meta_title = f"{keyword_clean} | KaziBoost"
            meta_description = f"Learn how {keyword_clean} helps Kenyan SMEs improve SEO, leads, and conversions."

        content = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "keyword": keyword_clean,
            "content_type": content_type,
            "tone": tone,
            "language": language,
            "length": length,
            "title": title,
            "meta_title": meta_title,
            "meta_description": meta_description,
            "body": body,
            "related_terms": related_terms,
        }
        self.seo_persistence.save_generated_content(content)
        return content

    def get_generated_content_history(self, tenant_id: str, limit: int = 20) -> list[dict[str, object]]:
        return self.seo_persistence.list_generated_content(tenant_id=tenant_id, limit=limit)

    def create_content_calendar_item(
        self,
        tenant_id: str,
        title: str,
        keyword: str,
        scheduled_for: str,
        language: str,
    ) -> ContentCalendarItem:
        item = ContentCalendarItem(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            title=title,
            keyword=keyword,
            scheduled_for=scheduled_for,
            language=language,
            status="scheduled",
            created_at=self._now_iso(),
        )
        self.seo_calendar[item.id] = item
        self.seo_calendar_by_tenant.setdefault(tenant_id, []).append(item.id)
        return item

    def list_content_calendar_items(self, tenant_id: str) -> list[ContentCalendarItem]:
        ids = self.seo_calendar_by_tenant.get(tenant_id, [])
        return [self.seo_calendar[item_id] for item_id in reversed(ids)]

    def render_metrics_prometheus(self) -> str:
        lines = [
            f"kaziboost_auth_logins_total {self.metrics['auth_logins_total']}",
            f"kaziboost_whatsapp_events_total {self.metrics['whatsapp_events_total']}",
            f"kaziboost_payments_callbacks_total {self.metrics['payments_callbacks_total']}",
        ]
        return "\n".join(lines) + "\n"

    def onboarding_checklist(self, tenant_id: str) -> dict[str, object]:
        items = {
            "site_published": any(site.tenant_id == tenant_id and site.status == "published" for site in self.sites.values()),
            "first_lead_captured": len(self.contacts_by_tenant.get(tenant_id, [])) > 0,
            "whatsapp_connected": len(self.whatsapp_by_tenant.get(tenant_id, [])) > 0,
            "first_payment_created": any(payment.tenant_id == tenant_id for payment in self.payments.values()),
            "seo_content_generated": len(self.get_generated_content_history(tenant_id=tenant_id, limit=1)) > 0,
        }
        completed = sum(1 for value in items.values() if value)
        return {"completed": completed, "total": len(items), "items": items}

    def analytics_dashboard(self, tenant_id: str) -> dict[str, int]:
        total_leads = len(self.contacts_by_tenant.get(tenant_id, []))
        open_conversations = len(
            [
                thread_id
                for thread_id in self.whatsapp_by_tenant.get(tenant_id, [])
                if self.whatsapp_conversations[thread_id].status == "open"
            ]
        )
        successful_payments = len(
            [payment for payment in self.payments.values() if payment.tenant_id == tenant_id and payment.status == "success"]
        )
        published_sites = len(
            [site for site in self.sites.values() if site.tenant_id == tenant_id and site.status == "published"]
        )
        return {
            "total_leads": total_leads,
            "open_conversations": open_conversations,
            "successful_payments": successful_payments,
            "published_sites": published_sites,
        }

    def analytics_funnel(self, tenant_id: str) -> dict[str, object]:
        leads = len(self.contacts_by_tenant.get(tenant_id, []))
        conversations = len(self.whatsapp_by_tenant.get(tenant_id, []))
        successful_payments = len(
            [payment for payment in self.payments.values() if payment.tenant_id == tenant_id and payment.status == "success"]
        )

        lead_to_conversation_rate = (conversations / leads) if leads else 0.0
        lead_to_payment_rate = (successful_payments / leads) if leads else 0.0

        return {
            "stages": {
                "leads": leads,
                "conversations": conversations,
                "successful_payments": successful_payments,
            },
            "conversion": {
                "lead_to_conversation_rate": round(lead_to_conversation_rate, 4),
                "lead_to_payment_rate": round(lead_to_payment_rate, 4),
            },
        }

    def create_training_article(self, tenant_id: str, title: str, content: str, category: str) -> TrainingArticle:
        article = TrainingArticle(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            title=title,
            content=content,
            category=category,
            created_at=self._now_iso(),
        )
        self.training_articles[article.id] = article
        self.training_by_tenant.setdefault(tenant_id, []).append(article.id)
        return article

    def search_training_articles(self, tenant_id: str, query: str) -> list[TrainingArticle]:
        q = query.strip().lower()
        items = [self.training_articles[item_id] for item_id in self.training_by_tenant.get(tenant_id, [])]
        return [item for item in items if q in item.title.lower() or q in item.content.lower() or q in item.category.lower()]

    def update_training_article(
        self,
        tenant_id: str,
        article_id: str,
        title: str | None = None,
        content: str | None = None,
        category: str | None = None,
    ) -> TrainingArticle:
        article = self.training_articles.get(article_id)
        if not article or article.tenant_id != tenant_id:
            raise ValueError("Article not found")
        if title is not None:
            article.title = title
        if content is not None:
            article.content = content
        if category is not None:
            article.category = category
        return article

    def list_training_categories(self, tenant_id: str) -> list[str]:
        items = [self.training_articles[item_id] for item_id in self.training_by_tenant.get(tenant_id, [])]
        return sorted({item.category for item in items})

    def analytics_export_csv(self, tenant_id: str) -> str:
        metrics = self.analytics_dashboard(tenant_id=tenant_id)
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["metric", "value"])
        for metric, value in metrics.items():
            writer.writerow([metric, value])
        return output.getvalue()

    def schedule_report(self, tenant_id: str, email: str, frequency: str) -> dict[str, str]:
        schedule = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "email": email,
            "frequency": frequency,
            "status": "scheduled",
        }
        self.report_schedules.setdefault(tenant_id, []).append(schedule)
        return schedule

    def list_report_schedules(self, tenant_id: str) -> list[dict[str, str]]:
        return list(self.report_schedules.get(tenant_id, []))

    def cancel_report_schedule(self, tenant_id: str, schedule_id: str) -> dict[str, str]:
        items = self.report_schedules.get(tenant_id, [])
        for item in items:
            if item["id"] == schedule_id:
                item["status"] = "cancelled"
                return item
        raise ValueError("Schedule not found")


store = InMemoryStore(db_path=os.getenv("KAZIBOOST_DB_PATH"))
