from __future__ import annotations

import csv
import io
import os
import re
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from .passwords import hash_password, needs_rehash, verify_password
from .repositories import GeneratedContentRepository, SEOGeneratedContentRepository
from .seo_persistence import SEOPersistence


CONTACT_REDACTION_MARKER = "[redacted: contact anonymized]"


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
    custom_domain: str | None = None


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
class ContactNote:
    id: str
    tenant_id: str
    contact_id: str
    text: str
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
    failure_reason: str | None = None


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
    featured: bool = False
    views: int = 0


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
    generated_content_id: str | None = None


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
        self.user_mfa: dict[str, dict[str, object]] = {}
        self.mfa_challenges: dict[str, dict[str, str]] = {}

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
        self.contact_notes: dict[str, ContactNote] = {}
        self.contact_notes_by_contact: dict[str, list[str]] = {}
        self.interactions: dict[str, InteractionEvent] = {}
        self.interactions_by_contact: dict[str, list[str]] = {}

        self.keyword_workspaces: dict[str, dict[str, list[str]]] = {}
        self.seo_calendar: dict[str, ContentCalendarItem] = {}
        self.seo_calendar_by_tenant: dict[str, list[str]] = {}
        self.seo_persistence = SEOPersistence(db_path=db_path)
        self.generated_content_repository: GeneratedContentRepository = SEOGeneratedContentRepository(self.seo_persistence)

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
        self.analytics_connectors: dict[str, list[dict[str, str]]] = {}
        self.payment_providers: dict[str, list[dict[str, str]]] = {}

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

    def list_audit_events(
        self,
        tenant_id: str,
        limit: int = 100,
        event_type: str | None = None,
        entity_type: str | None = None,
    ) -> list[AuditEvent]:
        event_ids = self.audit_by_tenant.get(tenant_id, [])[-limit:]
        items = [self.audit_events[event_id] for event_id in reversed(event_ids)]
        if event_type:
            items = [item for item in items if item.event_type == event_type]
        if entity_type:
            items = [item for item in items if item.entity_type == entity_type]
        return items

    def create_tenant_and_owner(self, business_name: str, owner_name: str, email: str, password: str) -> tuple[Tenant, User]:
        normalized_email = email.strip().lower()
        if normalized_email in self.users_by_email:
            raise ValueError("Email already exists")
        if not self._password_is_strong(password):
            raise ValueError("Password must include upper/lowercase letters, number, symbol, and be at least 10 chars")

        tenant = Tenant(id=str(uuid.uuid4()), name=business_name)
        user = User(
            id=str(uuid.uuid4()),
            tenant_id=tenant.id,
            owner_name=owner_name,
            email=normalized_email,
            role="owner",
            password_hash=hash_password(password),
            password_salt="",
        )
        self.tenants[tenant.id] = tenant
        self.users_by_id[user.id] = user
        self.users_by_email[user.email] = user
        return tenant, user

    def update_tenant_profile(
        self,
        tenant_id: str,
        user_id: str,
        business_name: str,
        owner_name: str,
        actor_user_id: str | None = None,
    ) -> tuple[Tenant, User]:
        tenant = self.tenants.get(tenant_id)
        user = self.users_by_id.get(user_id)
        if not tenant or not user or user.tenant_id != tenant_id:
            raise ValueError("Tenant not found")

        tenant.name = business_name
        user.owner_name = owner_name
        self.record_audit_event(
            tenant_id=tenant_id,
            event_type="tenant.profile.updated",
            entity_type="tenant",
            entity_id=tenant_id,
            actor_user_id=actor_user_id,
            metadata={"business_name": business_name, "owner_name": owner_name},
        )
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

        user = User(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            owner_name=owner_name,
            email=normalized_email,
            role=role,
            password_hash=hash_password(password),
            password_salt="",
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
        if not user or not verify_password(password, user.password_hash, legacy_salt=user.password_salt):
            failure = self.login_failures.setdefault(normalized_email, {"count": 0, "blocked_until": None})
            failure["count"] = int(failure["count"]) + 1
            if int(failure["count"]) >= 5:
                failure["blocked_until"] = datetime.now(tz=UTC) + timedelta(minutes=self.login_block_minutes)
            return None

        if needs_rehash(user.password_hash):
            user.password_hash = hash_password(password)
            user.password_salt = ""
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

    def enroll_mfa(self, user_id: str) -> dict[str, object]:
        secret = secrets.token_hex(8)
        backup_codes = [secrets.token_hex(3) for _ in range(3)]
        payload = {"secret": secret, "enabled": True, "backup_codes": backup_codes}
        self.user_mfa[user_id] = payload
        return payload

    def create_mfa_challenge(self, user_id: str) -> dict[str, str]:
        if user_id not in self.user_mfa:
            raise ValueError("MFA is not enabled")
        challenge_id = str(uuid.uuid4())
        code = secrets.token_hex(3)
        challenge = {"challenge_id": challenge_id, "user_id": user_id, "code": code, "status": "pending"}
        self.mfa_challenges[challenge_id] = challenge
        return challenge

    def verify_mfa_challenge(self, user_id: str, challenge_id: str, code: str) -> dict[str, str]:
        challenge = self.mfa_challenges.get(challenge_id)
        if not challenge or challenge["user_id"] != user_id:
            raise ValueError("MFA challenge not found")
        valid_codes = [challenge["code"], *self.user_mfa.get(user_id, {}).get("backup_codes", [])]
        if code not in valid_codes:
            raise ValueError("Invalid MFA code")
        challenge["status"] = "verified"
        return challenge

    def force_expire_token_for_test(self, token: str) -> None:
        session = self.tokens.get(token)
        if not session:
            return
        session.expires_at = datetime.now(tz=UTC) - timedelta(seconds=1)

    def list_sites(self, tenant_id: str, status: str | None = None) -> list[Site]:
        items = [site for site in self.sites.values() if site.tenant_id == tenant_id]
        if status:
            items = [site for site in items if site.status == status]
        return items

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

    def delete_site(self, tenant_id: str, site_id: str) -> None:
        site = self.get_site(tenant_id, site_id)
        for page_id in self.pages_by_site.get(site.id, []):
            self.pages.pop(page_id, None)
        self.pages_by_site.pop(site.id, None)
        self.seo_assets.pop(site.id, None)
        self.sites.pop(site.id, None)

    def get_site(self, tenant_id: str, site_id: str) -> Site:
        site = self.sites.get(site_id)
        if not site or site.tenant_id != tenant_id:
            raise ValueError("Site not found")
        return site

    def unpublish_site(self, tenant_id: str, site_id: str) -> Site:
        site = self.get_site(tenant_id, site_id)
        site.status = "draft"
        site.published_url = None
        self.seo_assets.pop(site_id, None)
        return site

    def add_page(self, tenant_id: str, site_id: str, slug: str, title: str, language: str, body_blocks: list[str]) -> Page:
        self.get_site(tenant_id, site_id)
        existing_page_ids = self.pages_by_site.get(site_id, [])
        for page_id in existing_page_ids:
            existing = self.pages[page_id]
            if existing.slug == slug and existing.language == language:
                raise ValueError("Page slug already exists for language")

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

    def get_page_by_slug(self, tenant_id: str, site_id: str, slug: str, language: str | None = None) -> Page:
        site = self.get_site(tenant_id, site_id)
        candidates: list[Page] = []
        for page_id in self.pages_by_site.get(site_id, []):
            page = self.pages[page_id]
            if page.slug == slug:
                candidates.append(page)
        if language:
            for page in candidates:
                if page.language == language:
                    return page
        for page in candidates:
            if page.language == site.primary_language:
                return page
        if candidates:
            return candidates[0]
        raise ValueError("Page not found")

    def get_site_page(self, tenant_id: str, site_id: str, page_id: str) -> Page:
        self.get_site(tenant_id, site_id)
        page = self.pages.get(page_id)
        if not page or page.tenant_id != tenant_id or page.site_id != site_id:
            raise ValueError("Page not found")
        return page

    def _site_pages(self, site_id: str) -> list[Page]:
        return [self.pages[page_id] for page_id in self.pages_by_site.get(site_id, [])]

    def list_site_pages(self, tenant_id: str, site_id: str, language: str | None = None) -> list[Page]:
        self.get_site(tenant_id, site_id)
        items = self._site_pages(site_id)
        if language:
            items = [item for item in items if item.language == language]
        return items

    def publish_site(self, tenant_id: str, site_id: str) -> Site:
        site = self.get_site(tenant_id, site_id)
        pages = self._site_pages(site_id)
        if not pages:
            raise ValueError("Cannot publish site without pages")

        base_domain = site.custom_domain or f"{site.id}.kaziboost.local"
        published_url = f"https://{base_domain}"
        site.published_url = published_url
        site.status = "published"

        urls_xml = []
        seen_paths: set[str] = set()
        for page in pages:
            path = "/" if page.slug == "home" else f"/{page.slug}"
            if path in seen_paths:
                continue
            seen_paths.add(path)
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
        seen: set[tuple[str, str]] = set()
        for page in self._site_pages(site_id):
            path = "/" if page.slug == "home" else f"/{page.slug}"
            key = (page.slug, page.language)
            if key in seen:
                continue
            seen.add(key)
            items.append({"language": page.language, "slug": page.slug, "href": f"{site.published_url}{path}?language={page.language}"})
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

    def list_contacts(
        self,
        tenant_id: str,
        source: str | None = None,
        tag: str | None = None,
        email_marketing: bool | None = None,
    ) -> list[Contact]:
        items = [self.contacts[contact_id] for contact_id in self.contacts_by_tenant.get(tenant_id, [])]
        if source:
            items = [contact for contact in items if contact.source == source]
        if tag:
            items = [contact for contact in items if tag in contact.tags]
        if email_marketing is not None:
            items = [contact for contact in items if contact.consent.get("email_marketing") is email_marketing]
        return items

    def search_contacts(self, tenant_id: str, query: str) -> list[Contact]:
        q = query.strip().lower()
        items = [self.contacts[contact_id] for contact_id in self.contacts_by_tenant.get(tenant_id, [])]
        return [
            contact for contact in items
            if q in contact.name.lower() or q in contact.email.lower() or q in contact.phone.lower()
        ]

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

    def update_contact_tags(self, tenant_id: str, contact_id: str, tags: list[str], actor_user_id: str | None = None) -> Contact:
        contact = self.get_contact(tenant_id=tenant_id, contact_id=contact_id)
        normalized_tags = sorted({tag.strip() for tag in tags if tag.strip()})
        contact.tags = normalized_tags
        self.record_audit_event(
            tenant_id=tenant_id,
            event_type="contact.tags.updated",
            entity_type="contact",
            entity_id=contact_id,
            actor_user_id=actor_user_id,
            metadata={"tags": ",".join(normalized_tags)},
        )
        return contact

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

    def get_segment_contact_count(self, tenant_id: str, segment_id: str) -> int:
        return len(self.get_segment_contacts(tenant_id=tenant_id, segment_id=segment_id))

    def list_segments(self, tenant_id: str) -> list[CRMSegment]:
        ids = self.crm_segments_by_tenant.get(tenant_id, [])
        return [self.crm_segments[item_id] for item_id in ids if item_id in self.crm_segments]

    def get_segment(self, tenant_id: str, segment_id: str) -> CRMSegment:
        segment = self.crm_segments.get(segment_id)
        if not segment or segment.tenant_id != tenant_id:
            raise ValueError("Segment not found")
        return segment

    def update_segment(
        self,
        tenant_id: str,
        segment_id: str,
        name: str | None = None,
        tag: str | None = None,
        source: str | None = None,
    ) -> CRMSegment:
        segment = self.crm_segments.get(segment_id)
        if not segment or segment.tenant_id != tenant_id:
            raise ValueError("Segment not found")
        if name is not None:
            segment.name = name
        segment.tag = tag
        segment.source = source
        return segment

    def delete_segment(self, tenant_id: str, segment_id: str) -> None:
        segment = self.crm_segments.get(segment_id)
        if not segment or segment.tenant_id != tenant_id:
            raise ValueError("Segment not found")
        self.crm_segments.pop(segment_id, None)
        self.crm_segments_by_tenant[tenant_id] = [item_id for item_id in self.crm_segments_by_tenant.get(tenant_id, []) if item_id != segment_id]

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

    def campaign_history(
        self,
        tenant_id: str,
        channel: str | None = None,
        subject: str | None = None,
    ) -> list[CampaignDispatch]:
        ids = self.campaigns_by_tenant.get(tenant_id, [])
        items = [self.campaign_dispatches[c_id] for c_id in reversed(ids)]
        if channel:
            items = [item for item in items if item.channel == channel]
        if subject:
            lowered = subject.strip().lower()
            items = [item for item in items if lowered in item.subject.lower()]
        return items

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

    def lead_sources_summary(self, tenant_id: str) -> dict[str, dict[str, int]]:
        contacts = [self.contacts[item_id] for item_id in self.contacts_by_tenant.get(tenant_id, [])]
        totals: dict[str, int] = {}
        for contact in contacts:
            totals[contact.source] = totals.get(contact.source, 0) + 1
        return {"totals": totals}

    def contact_tags_summary(self, tenant_id: str) -> dict[str, dict[str, int]]:
        contacts = [self.contacts[item_id] for item_id in self.contacts_by_tenant.get(tenant_id, [])]
        totals: dict[str, int] = {}
        for contact in contacts:
            for tag in contact.tags:
                totals[tag] = totals.get(tag, 0) + 1
        return {"totals": totals}

    def get_contact(self, tenant_id: str, contact_id: str) -> Contact:
        contact = self.contacts.get(contact_id)
        if not contact or contact.tenant_id != tenant_id:
            raise ValueError("Contact not found")
        return contact

    def get_contact_timeline(self, tenant_id: str, contact_id: str) -> list[InteractionEvent]:
        self.get_contact(tenant_id, contact_id)
        event_ids = self.interactions_by_contact.get(contact_id, [])
        return [self.interactions[event_id] for event_id in event_ids]

    def add_contact_note(self, tenant_id: str, contact_id: str, text: str) -> ContactNote:
        self.get_contact(tenant_id, contact_id)
        note = ContactNote(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            contact_id=contact_id,
            text=text,
            created_at=self._now_iso(),
        )
        self.contact_notes[note.id] = note
        self.contact_notes_by_contact.setdefault(contact_id, []).append(note.id)
        return note

    def list_contact_notes(self, tenant_id: str, contact_id: str) -> list[ContactNote]:
        self.get_contact(tenant_id, contact_id)
        ids = self.contact_notes_by_contact.get(contact_id, [])
        return [self.contact_notes[item_id] for item_id in reversed(ids)]

    def _redact_contact_activity(self, contact_id: str) -> None:
        for event_id in self.interactions_by_contact.get(contact_id, []):
            self.interactions[event_id].message = CONTACT_REDACTION_MARKER
        for note_id in self.contact_notes_by_contact.get(contact_id, []):
            self.contact_notes[note_id].text = CONTACT_REDACTION_MARKER

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
        self._redact_contact_activity(contact_id=contact.id)
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

    def list_whatsapp_conversations(
        self,
        tenant_id: str,
        status: str | None = None,
        assigned_to: str | None = None,
        from_phone: str | None = None,
    ) -> list[WhatsAppConversation]:
        thread_ids = self.whatsapp_by_tenant.get(tenant_id, [])
        items = [self.whatsapp_conversations[thread_id] for thread_id in thread_ids]
        if status:
            items = [item for item in items if item.status == status]
        if assigned_to:
            items = [item for item in items if item.assigned_to == assigned_to]
        if from_phone:
            items = [item for item in items if item.from_phone == from_phone]
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

    def list_whatsapp_reminders(
        self,
        tenant_id: str,
        status: str | None = None,
        thread_id: str | None = None,
    ) -> list[WhatsAppReminder]:
        ids = self.whatsapp_reminders_by_tenant.get(tenant_id, [])
        items = [self.whatsapp_reminders[item_id] for item_id in reversed(ids)]
        if status:
            items = [item for item in items if item.status == status]
        if thread_id:
            items = [item for item in items if item.thread_id == thread_id]
        return items

    def mark_whatsapp_reminder_sent(self, tenant_id: str, reminder_id: str) -> WhatsAppReminder:
        item = self.whatsapp_reminders.get(reminder_id)
        if not item or item.tenant_id != tenant_id:
            raise ValueError("Reminder not found")
        item.status = "sent"
        return item

    def overdue_whatsapp_queue(self, tenant_id: str) -> list[WhatsAppConversation]:
        items = self.list_whatsapp_conversations(tenant_id=tenant_id, status="open")
        return [item for item in items if item.assigned_to is None]

    def whatsapp_sla_stats(self, tenant_id: str) -> dict[str, dict[str, int]]:
        items = self.list_whatsapp_conversations(tenant_id=tenant_id)
        totals = {"all": len(items), "open": 0, "handoff": 0, "closed": 0}
        for item in items:
            if item.status in totals:
                totals[item.status] += 1
        return {"totals": totals}

    def add_whatsapp_faq(self, tenant_id: str, question: str, answer: str) -> dict[str, str]:
        item = {"question": question, "answer": answer}
        self.whatsapp_faq_by_tenant.setdefault(tenant_id, []).append(item)
        return item

    def list_whatsapp_faq(self, tenant_id: str) -> list[dict[str, str]]:
        return list(self.whatsapp_faq_by_tenant.get(tenant_id, []))

    def delete_whatsapp_faq(self, tenant_id: str, faq_index: int) -> dict[str, str]:
        items = self.whatsapp_faq_by_tenant.get(tenant_id, [])
        if faq_index < 0 or faq_index >= len(items):
            raise ValueError("FAQ not found")
        return items.pop(faq_index)

    def whatsapp_bot_reply(self, tenant_id: str, thread_id: str, actor_user_id: str | None = None) -> dict[str, str]:
        conversation = self.whatsapp_conversations.get(thread_id)
        if not conversation or conversation.tenant_id != tenant_id:
            raise ValueError("Conversation not found")

        message = conversation.last_message.lower()
        faq_items = self.whatsapp_faq_by_tenant.get(tenant_id, [])
        for faq in faq_items:
            question = faq["question"].lower()
            if any(token in question for token in message.split() if len(token) > 3):
                reply = {"mode": "bot", "reply_text": faq["answer"], "thread_id": thread_id}
                self.record_audit_event(
                    tenant_id=tenant_id,
                    event_type="whatsapp.bot.replied",
                    entity_type="whatsapp_conversation",
                    entity_id=thread_id,
                    actor_user_id=actor_user_id,
                    metadata={"mode": reply["mode"]},
                )
                return reply

        reply = {
            "mode": "handoff_required",
            "reply_text": "I need a human teammate to help with this request.",
            "thread_id": thread_id,
        }
        self.record_audit_event(
            tenant_id=tenant_id,
            event_type="whatsapp.bot.replied",
            entity_type="whatsapp_conversation",
            entity_id=thread_id,
            actor_user_id=actor_user_id,
            metadata={"mode": reply["mode"]},
        )
        return reply

    def whatsapp_handoff(self, tenant_id: str, thread_id: str, assigned_to: str) -> WhatsAppConversation:
        conversation = self.whatsapp_conversations.get(thread_id)
        if not conversation or conversation.tenant_id != tenant_id:
            raise ValueError("Conversation not found")
        conversation.status = "handoff"
        conversation.assigned_to = assigned_to
        conversation.updated_at = self._now_iso()
        return conversation

    def whatsapp_assign(self, tenant_id: str, thread_id: str, assigned_to: str) -> WhatsAppConversation:
        conversation = self.whatsapp_conversations.get(thread_id)
        if not conversation or conversation.tenant_id != tenant_id:
            raise ValueError("Conversation not found")
        conversation.assigned_to = assigned_to
        conversation.updated_at = self._now_iso()
        return conversation

    def whatsapp_human_reply(self, tenant_id: str, thread_id: str, message: str, sent_by: str) -> dict[str, str]:
        conversation = self.whatsapp_conversations.get(thread_id)
        if not conversation or conversation.tenant_id != tenant_id:
            raise ValueError("Conversation not found")
        conversation.last_message = message
        conversation.status = "open"
        conversation.updated_at = self._now_iso()
        return {"thread_id": thread_id, "message": message, "sent_by": sent_by, "status": "sent"}

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
            failure_reason=None,
        )
        self.payments[payment.payment_id] = payment
        return payment

    def apply_mpesa_callback(
        self,
        tenant_id: str,
        payment_id: str,
        provider_tx_id: str,
        status: str,
        reason: str | None = None,
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
        payment.failure_reason = reason if status == "failed" else None
        self.record_audit_event(
            tenant_id=tenant_id,
            event_type="payment.callback.applied",
            entity_type="payment",
            entity_id=payment.payment_id,
            actor_user_id=actor_user_id,
            metadata={"status": status, "provider_tx_id": provider_tx_id, "reason": reason or ""},
        )
        return {"payment": payment, "idempotent": False}

    def list_payments_by_contact(
        self,
        tenant_id: str,
        contact_id: str,
        status: str | None = None,
        provider_tx_id: str | None = None,
    ) -> list[Payment]:
        items = [
            payment
            for payment in self.payments.values()
            if payment.tenant_id == tenant_id and payment.contact_id == contact_id
        ]
        if status:
            items = [payment for payment in items if payment.status == status]
        if provider_tx_id:
            items = [payment for payment in items if payment.provider_tx_id == provider_tx_id]
        return items

    def payments_reconciliation_summary(self, tenant_id: str, contact_id: str) -> dict[str, object]:
        items = self.list_payments_by_contact(tenant_id=tenant_id, contact_id=contact_id)
        by_status: dict[str, int] = {}
        total_amount = 0
        for item in items:
            by_status[item.status] = by_status.get(item.status, 0) + 1
            total_amount += item.amount
        return {
            "contact_id": contact_id,
            "total": len(items),
            "by_status": by_status,
            "total_amount": total_amount,
        }

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

    def refunds_report(self, tenant_id: str) -> dict[str, object]:
        items = [item for item in self.payment_refunds.values() if item.tenant_id == tenant_id]
        by_reason: dict[str, dict[str, int]] = {}
        for item in items:
            agg = by_reason.setdefault(item.reason, {"count": 0, "amount": 0})
            agg["count"] += 1
            agg["amount"] += item.amount
        return {"total_refunds": len(items), "by_reason": by_reason}

    def export_payments_csv(self, tenant_id: str) -> str:
        items = [item for item in self.payments.values() if item.tenant_id == tenant_id]
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["payment_id", "reference", "amount", "currency", "status", "provider_tx_id", "reason"])
        for item in items:
            writer.writerow([
                item.payment_id,
                item.reference,
                item.amount,
                item.currency,
                item.status,
                item.provider_tx_id or "",
                item.failure_reason or "",
            ])
        return output.getvalue()

    def failed_payments(self, tenant_id: str, reason: str | None = None) -> list[Payment]:
        items = [item for item in self.payments.values() if item.tenant_id == tenant_id and item.status == "failed"]
        if reason:
            items = [item for item in items if item.failure_reason == reason]
        return sorted(items, key=lambda x: x.created_at, reverse=True)

    def payments_summary(self, tenant_id: str) -> dict[str, object]:
        items = [payment for payment in self.payments.values() if payment.tenant_id == tenant_id]
        totals = {"count": len(items), "amount": sum(item.amount for item in items)}
        by_status: dict[str, dict[str, int]] = {}
        for payment in items:
            agg = by_status.setdefault(payment.status, {"count": 0, "amount": 0})
            agg["count"] += 1
            agg["amount"] += payment.amount
        return {"totals": totals, "by_status": by_status}

    def payments_monthly_report(self, tenant_id: str) -> dict[str, object]:
        now_month = datetime.now(tz=UTC).strftime("%Y-%m")
        items = [
            payment
            for payment in self.payments.values()
            if payment.tenant_id == tenant_id and payment.created_at.startswith(now_month)
        ]
        successful = [item for item in items if item.status == "success"]
        return {
            "month": now_month,
            "successful_count": len(successful),
            "successful_revenue": sum(item.amount for item in successful),
        }

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

    def rename_saved_keywords_workspace(self, tenant_id: str, workspace: str, new_workspace: str) -> dict[str, object]:
        current = self.get_saved_keywords(tenant_id=tenant_id, workspace=workspace)
        keywords = list(current["keywords"])
        self.save_keywords(tenant_id=tenant_id, workspace=new_workspace, keywords=keywords)
        self.delete_saved_keywords_workspace(tenant_id=tenant_id, workspace=workspace)
        return {"workspace": new_workspace, "count": len(keywords), "keywords": keywords}

    def list_keyword_workspaces(self, tenant_id: str) -> list[dict[str, object]]:
        tenant_workspaces = self.keyword_workspaces.setdefault(tenant_id, {})
        items = [
            {"workspace": workspace, "count": len(keywords)}
            for workspace, keywords in tenant_workspaces.items()
        ]
        return sorted(items, key=lambda item: item["workspace"])

    def delete_saved_keywords_workspace(self, tenant_id: str, workspace: str) -> None:
        tenant_workspaces = self.keyword_workspaces.setdefault(tenant_id, {})
        tenant_workspaces.pop(workspace, None)
        self.seo_persistence.save_keywords(tenant_id=tenant_id, workspace=workspace, keywords=[])
        with self.seo_persistence._connect() as conn:  # noqa: SLF001
            conn.execute(
                "DELETE FROM seo_saved_keywords WHERE tenant_id = ? AND workspace = ?",
                (tenant_id, workspace),
            )

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
        prompt_version = "seo-deterministic-v1"
        generation_mode = "deterministic_template"
        safety_outcome = "safe"
        policy_violations: list[str] = []

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
            "prompt_version": prompt_version,
            "generation_mode": generation_mode,
            "safety_outcome": safety_outcome,
            "policy_violations": policy_violations,
            "status": "needs_review",
            "reviewed_by": None,
            "reviewed_at": None,
            "review_note": None,
        }
        self.generated_content_repository.save(content)
        return content

    def get_generated_content_history(
        self,
        tenant_id: str,
        limit: int = 20,
        language: str | None = None,
    ) -> list[dict[str, object]]:
        return self.generated_content_repository.list(tenant_id=tenant_id, limit=limit, language=language)

    def storage_ready(self) -> bool:
        return self.seo_persistence.check_ready()

    def update_generated_content_review(
        self,
        tenant_id: str,
        content_id: str,
        review_status: str,
        reviewed_by: str,
        review_note: str | None = None,
    ) -> dict[str, object]:
        content = self.generated_content_repository.get(tenant_id=tenant_id, record_id=content_id)
        if not content:
            raise ValueError("Generated content not found")
        current_status = str(content["status"])
        allowed = {
            "needs_review": {"approved", "rejected"},
            "rejected": {"needs_review"},
            "approved": set(),
        }
        if review_status not in allowed or review_status not in allowed[current_status]:
            raise ValueError("Invalid generated-content review transition")
        reviewed_at = self._now_iso()
        self.generated_content_repository.update_review(
            tenant_id=tenant_id,
            record_id=content_id,
            status=review_status,
            reviewed_by=reviewed_by,
            reviewed_at=reviewed_at,
            review_note=review_note,
        )
        updated = self.generated_content_repository.get(tenant_id=tenant_id, record_id=content_id)
        assert updated is not None
        return updated

    def generate_topic_map(self, seed_keyword: str, location: str, language: str) -> dict[str, object]:
        seed = seed_keyword.strip()
        seed_title = seed.title()
        if language == "sw":
            pillar_topic = f"Mwongozo wa {seed_title} kwa biashara za {location}"
            cluster_topics = [
                f"Jinsi ya kupata leads za {seed} {location}",
                f"SEO ya ndani kwa {seed} {location}",
                f"WhatsApp conversion kwa {seed} {location}",
                f"Bei na promosheni za {seed} {location}",
            ]
        else:
            pillar_topic = f"{seed_title} Growth Guide for {location} Businesses"
            cluster_topics = [
                f"Local SEO for {seed} in {location}",
                f"WhatsApp funnels for {seed}",
                f"Pricing strategy for {seed} in {location}",
                f"Landing pages that convert {seed} leads",
            ]
        internal_links = [
            {"from": pillar_topic, "to": cluster_topics[0], "anchor_text": f"{seed} local SEO"},
            {"from": pillar_topic, "to": cluster_topics[1], "anchor_text": f"{seed} WhatsApp funnel"},
            {"from": pillar_topic, "to": cluster_topics[2], "anchor_text": f"{seed} pricing guide"},
        ]
        return {
            "pillar_topic": pillar_topic,
            "cluster_topics": cluster_topics,
            "internal_links": internal_links,
        }

    def create_content_calendar_item(
        self,
        tenant_id: str,
        title: str,
        keyword: str,
        scheduled_for: str,
        language: str,
        generated_content_id: str | None = None,
    ) -> ContentCalendarItem:
        if generated_content_id:
            content = self.generated_content_repository.get(tenant_id=tenant_id, record_id=generated_content_id)
            if not content:
                raise ValueError("Generated content not found")
            initial_status = "draft" if content["status"] != "approved" else "scheduled"
        else:
            initial_status = "scheduled"
        item = ContentCalendarItem(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            title=title,
            keyword=keyword,
            scheduled_for=scheduled_for,
            language=language,
            status=initial_status,
            created_at=self._now_iso(),
            generated_content_id=generated_content_id,
        )
        self.seo_calendar[item.id] = item
        self.seo_calendar_by_tenant.setdefault(tenant_id, []).append(item.id)
        return item

    def list_content_calendar_items(
        self,
        tenant_id: str,
        status: str | None = None,
        language: str | None = None,
        on_or_after: str | None = None,
        on_or_before: str | None = None,
    ) -> list[ContentCalendarItem]:
        ids = self.seo_calendar_by_tenant.get(tenant_id, [])
        items = [self.seo_calendar[item_id] for item_id in reversed(ids)]
        if status:
            items = [item for item in items if item.status == status]
        if language:
            items = [item for item in items if item.language == language]
        if on_or_after:
            items = [item for item in items if item.scheduled_for >= on_or_after]
        if on_or_before:
            items = [item for item in items if item.scheduled_for <= on_or_before]
        return items

    def update_content_calendar_status(self, tenant_id: str, item_id: str, status: str) -> ContentCalendarItem:
        item = self.seo_calendar.get(item_id)
        if not item or item.tenant_id != tenant_id:
            raise ValueError("Calendar item not found")
        if status not in {"draft", "scheduled", "published", "cancelled"}:
            raise ValueError("Invalid calendar status")
        if status in {"scheduled", "published"} and item.generated_content_id:
            content = self.generated_content_repository.get(tenant_id=tenant_id, record_id=item.generated_content_id)
            if not content:
                raise ValueError("Generated content not found")
            if content["status"] != "approved":
                raise ValueError("Generated content must be approved before scheduling or publishing")
        item.status = status
        return item

    def due_calendar_items(self, tenant_id: str, on_or_before: str) -> list[ContentCalendarItem]:
        items = self.list_content_calendar_items(tenant_id=tenant_id)
        return [item for item in items if item.scheduled_for <= on_or_before and item.status == "scheduled"]

    def delete_content_calendar_item(self, tenant_id: str, item_id: str) -> None:
        item = self.seo_calendar.get(item_id)
        if not item or item.tenant_id != tenant_id:
            raise ValueError("Calendar item not found")
        self.seo_calendar.pop(item_id, None)
        self.seo_calendar_by_tenant[tenant_id] = [existing_id for existing_id in self.seo_calendar_by_tenant.get(tenant_id, []) if existing_id != item_id]

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

    def onboarding_recommendations(self, tenant_id: str) -> list[dict[str, str]]:
        checklist = self.onboarding_checklist(tenant_id=tenant_id)["items"]
        recommendations: list[dict[str, str]] = []
        if not checklist["site_published"]:
            recommendations.append({"key": "publish_site", "title": "Publish your first site", "action": "/v1/sites"})
        if not checklist["seo_content_generated"]:
            recommendations.append({"key": "generate_seo", "title": "Generate your first SEO article", "action": "/v1/seo/content/generate"})
        if not checklist["first_lead_captured"]:
            recommendations.append({"key": "capture_lead", "title": "Create a CRM form and capture a lead", "action": "/v1/crm/forms"})
        if not checklist["whatsapp_connected"]:
            recommendations.append({"key": "connect_whatsapp", "title": "Connect WhatsApp and handle your first chat", "action": "/v1/whatsapp/webhook/incoming"})
        if not checklist["first_payment_created"]:
            recommendations.append({"key": "create_payment", "title": "Create your first payment flow", "action": "/v1/payments/mpesa/initiate"})
        return recommendations

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

    def analytics_trend_snapshot(self, tenant_id: str, days: int) -> dict[str, object]:
        total_leads = len(self.contacts_by_tenant.get(tenant_id, []))
        total_payments = len([p for p in self.payments.values() if p.tenant_id == tenant_id and p.status == "success"])
        today = datetime.now(tz=UTC).date()
        series = []
        for i in range(days):
            day = today - timedelta(days=(days - i - 1))
            series.append({"date": day.isoformat(), "leads": total_leads, "payments": total_payments})
        return {"days": days, "series": series}

    def analytics_dashboard_summary(self, tenant_id: str, days: int) -> dict[str, object]:
        return {
            "kpis": self.analytics_dashboard(tenant_id=tenant_id),
            "trend": self.analytics_trend_snapshot(tenant_id=tenant_id, days=days),
        }

    def create_training_article(self, tenant_id: str, title: str, content: str, category: str) -> TrainingArticle:
        article = TrainingArticle(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            title=title,
            content=content,
            category=category,
            created_at=self._now_iso(),
            featured=False,
            views=0,
        )
        self.training_articles[article.id] = article
        self.training_by_tenant.setdefault(tenant_id, []).append(article.id)
        return article

    def duplicate_training_article(self, tenant_id: str, article_id: str) -> TrainingArticle:
        article = self.training_articles.get(article_id)
        if not article or article.tenant_id != tenant_id:
            raise ValueError("Article not found")
        return self.create_training_article(
            tenant_id=tenant_id,
            title=f"{article.title} (Copy)",
            content=article.content,
            category=article.category,
        )

    def search_training_articles(
        self,
        tenant_id: str,
        query: str,
        category: str | None = None,
        limit: int | None = None,
    ) -> list[TrainingArticle]:
        q = query.strip().lower()
        items = [self.training_articles[item_id] for item_id in self.training_by_tenant.get(tenant_id, [])]
        items = [item for item in items if q in item.title.lower() or q in item.content.lower() or q in item.category.lower()]
        if category:
            items = [item for item in items if item.category == category]
        if limit is not None:
            items = items[:limit]
        return items

    def update_training_article(
        self,
        tenant_id: str,
        article_id: str,
        title: str | None = None,
        content: str | None = None,
        category: str | None = None,
        featured: bool | None = None,
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
        if featured is not None:
            article.featured = featured
        return article

    def list_training_categories(self, tenant_id: str) -> list[str]:
        items = [self.training_articles[item_id] for item_id in self.training_by_tenant.get(tenant_id, [])]
        return sorted({item.category for item in items})

    def list_training_articles(
        self,
        tenant_id: str,
        featured: bool | None = None,
        category: str | None = None,
    ) -> list[TrainingArticle]:
        ids = self.training_by_tenant.get(tenant_id, [])
        items = [self.training_articles[item_id] for item_id in reversed(ids) if item_id in self.training_articles]
        if featured is not None:
            items = [item for item in items if item.featured == featured]
        if category:
            items = [item for item in items if item.category == category]
        return items

    def delete_training_article(self, tenant_id: str, article_id: str) -> None:
        article = self.training_articles.get(article_id)
        if not article or article.tenant_id != tenant_id:
            raise ValueError("Article not found")
        self.training_articles.pop(article_id, None)
        self.training_by_tenant[tenant_id] = [item_id for item_id in self.training_by_tenant.get(tenant_id, []) if item_id != article_id]

    def get_training_article(self, tenant_id: str, article_id: str) -> TrainingArticle:
        article = self.training_articles.get(article_id)
        if not article or article.tenant_id != tenant_id:
            raise ValueError("Article not found")
        article.views += 1
        return article

    def top_training_articles(self, tenant_id: str, limit: int = 10, category: str | None = None) -> list[TrainingArticle]:
        items = self.list_training_articles(tenant_id=tenant_id, category=category)
        return sorted(items, key=lambda x: x.views, reverse=True)[:limit]

    def related_training_articles(self, tenant_id: str, article_id: str, limit: int = 5) -> list[TrainingArticle]:
        article = self.get_training_article(tenant_id=tenant_id, article_id=article_id)
        items = [
            item for item in self.list_training_articles(tenant_id=tenant_id, category=article.category)
            if item.id != article.id
        ]
        return items[:limit]

    def analytics_export_csv(self, tenant_id: str) -> str:
        metrics = self.analytics_dashboard(tenant_id=tenant_id)
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["metric", "value"])
        for metric, value in metrics.items():
            writer.writerow([metric, value])
        return output.getvalue()

    def analytics_export_pdf(self, tenant_id: str) -> bytes:
        metrics = self.analytics_dashboard(tenant_id=tenant_id)
        lines = ["KaziBoost Analytics Report", ""] + [f"{metric}: {value}" for metric, value in metrics.items()]
        body = "\n".join(lines)
        return body.encode("utf-8")

    def list_site_templates(self) -> list[dict[str, str]]:
        return [
            {"key": "salon-modern", "name": "Salon Modern", "category": "beauty", "primary_language": "en"},
            {"key": "hardware-shop", "name": "Hardware Shop", "category": "retail", "primary_language": "sw"},
            {"key": "clinic-basic", "name": "Clinic Basic", "category": "health", "primary_language": "en"},
            {"key": "restaurant-fast", "name": "Restaurant Fast", "category": "food", "primary_language": "en"},
            {"key": "tutor-pro", "name": "Tutor Pro", "category": "education", "primary_language": "en"},
        ]

    def create_site_domain(self, tenant_id: str, site_id: str, domain: str) -> Site:
        site = self.get_site(tenant_id, site_id)
        normalized = domain.strip().lower()
        if not re.fullmatch(r"[a-z0-9.-]+\.[a-z]{2,}", normalized):
            raise ValueError("Invalid domain")
        site.custom_domain = normalized
        if site.status == "published":
            self.publish_site(tenant_id=tenant_id, site_id=site_id)
        return site

    def create_analytics_connector(self, tenant_id: str, provider: str, property_id: str, status: str) -> dict[str, str]:
        connector = {
            "id": str(uuid.uuid4()),
            "provider": provider,
            "property_id": property_id,
            "status": status,
        }
        self.analytics_connectors.setdefault(tenant_id, []).append(connector)
        return connector

    def list_analytics_connectors(
        self,
        tenant_id: str,
        provider: str | None = None,
        status: str | None = None,
    ) -> list[dict[str, str]]:
        items = list(self.analytics_connectors.get(tenant_id, []))
        if provider:
            items = [item for item in items if item["provider"] == provider]
        if status:
            items = [item for item in items if item["status"] == status]
        return items

    def update_analytics_connector(self, tenant_id: str, connector_id: str, status: str) -> dict[str, str]:
        items = self.analytics_connectors.get(tenant_id, [])
        for item in items:
            if item["id"] == connector_id:
                item["status"] = status
                return item
        raise ValueError("Connector not found")

    def delete_analytics_connector(self, tenant_id: str, connector_id: str) -> dict[str, str]:
        items = self.analytics_connectors.get(tenant_id, [])
        for index, item in enumerate(items):
            if item["id"] == connector_id:
                return items.pop(index)
        raise ValueError("Connector not found")

    def create_payment_provider(self, tenant_id: str, provider: str, channel: str, status: str) -> dict[str, str]:
        item = {
            "id": str(uuid.uuid4()),
            "provider": provider,
            "channel": channel,
            "status": status,
        }
        self.payment_providers.setdefault(tenant_id, []).append(item)
        return item

    def list_payment_providers(
        self,
        tenant_id: str,
        status: str | None = None,
    ) -> list[dict[str, str]]:
        items = list(self.payment_providers.get(tenant_id, []))
        if status:
            items = [item for item in items if item["status"] == status]
        return items

    def update_payment_provider(self, tenant_id: str, provider_id: str, status: str) -> dict[str, str]:
        items = self.payment_providers.get(tenant_id, [])
        for item in items:
            if item["id"] == provider_id:
                item["status"] = status
                return item
        raise ValueError("Payment provider not found")

    def delete_payment_provider(self, tenant_id: str, provider_id: str) -> dict[str, str]:
        items = self.payment_providers.get(tenant_id, [])
        for index, item in enumerate(items):
            if item["id"] == provider_id:
                return items.pop(index)
        raise ValueError("Payment provider not found")

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

    def list_report_schedules(
        self,
        tenant_id: str,
        status: str | None = None,
        frequency: str | None = None,
    ) -> list[dict[str, str]]:
        items = list(self.report_schedules.get(tenant_id, []))
        if status:
            items = [item for item in items if item["status"] == status]
        if frequency:
            items = [item for item in items if item["frequency"] == frequency]
        return items

    def update_report_schedule(self, tenant_id: str, schedule_id: str, frequency: str) -> dict[str, str]:
        items = self.report_schedules.get(tenant_id, [])
        for item in items:
            if item["id"] == schedule_id:
                item["frequency"] = frequency
                return item
        raise ValueError("Schedule not found")

    def cancel_report_schedule(self, tenant_id: str, schedule_id: str) -> dict[str, str]:
        items = self.report_schedules.get(tenant_id, [])
        for item in items:
            if item["id"] == schedule_id:
                item["status"] = "cancelled"
                return item
        raise ValueError("Schedule not found")


store = InMemoryStore(db_path=os.getenv("KAZIBOOST_DB_PATH"))
