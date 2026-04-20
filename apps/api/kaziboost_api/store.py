from __future__ import annotations

import csv
import hashlib
import io
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime


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


class InMemoryStore:
    def __init__(self) -> None:
        self.tenants: dict[str, Tenant] = {}
        self.users_by_id: dict[str, User] = {}
        self.users_by_email: dict[str, User] = {}
        self.tokens: dict[str, str] = {}

        self.sites: dict[str, Site] = {}
        self.pages: dict[str, Page] = {}
        self.pages_by_site: dict[str, list[str]] = {}
        self.seo_assets: dict[str, SEOAsset] = {}

        self.crm_forms: dict[str, CRMForm] = {}
        self.contacts: dict[str, Contact] = {}
        self.contacts_by_tenant: dict[str, list[str]] = {}
        self.interactions: dict[str, InteractionEvent] = {}
        self.interactions_by_contact: dict[str, list[str]] = {}

    @staticmethod
    def _hash_password(password: str) -> str:
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(tz=UTC).isoformat()

    def create_tenant_and_owner(self, business_name: str, owner_name: str, email: str, password: str) -> tuple[Tenant, User]:
        normalized_email = email.strip().lower()
        if normalized_email in self.users_by_email:
            raise ValueError("Email already exists")

        tenant = Tenant(id=str(uuid.uuid4()), name=business_name)
        user = User(
            id=str(uuid.uuid4()),
            tenant_id=tenant.id,
            owner_name=owner_name,
            email=normalized_email,
            role="owner",
            password_hash=self._hash_password(password),
        )
        self.tenants[tenant.id] = tenant
        self.users_by_id[user.id] = user
        self.users_by_email[user.email] = user
        return tenant, user

    def authenticate(self, email: str, password: str) -> tuple[str, User, Tenant] | None:
        normalized_email = email.strip().lower()
        user = self.users_by_email.get(normalized_email)
        if not user:
            return None
        if user.password_hash != self._hash_password(password):
            return None

        tenant = self.tenants[user.tenant_id]
        token = secrets.token_urlsafe(24)
        self.tokens[token] = user.id
        return token, user, tenant

    def resolve_token(self, token: str) -> tuple[User, Tenant] | None:
        user_id = self.tokens.get(token)
        if not user_id:
            return None
        user = self.users_by_id[user_id]
        tenant = self.tenants[user.tenant_id]
        return user, tenant

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

    def get_contact(self, tenant_id: str, contact_id: str) -> Contact:
        contact = self.contacts.get(contact_id)
        if not contact or contact.tenant_id != tenant_id:
            raise ValueError("Contact not found")
        return contact

    def get_contact_timeline(self, tenant_id: str, contact_id: str) -> list[InteractionEvent]:
        self.get_contact(tenant_id, contact_id)
        event_ids = self.interactions_by_contact.get(contact_id, [])
        return [self.interactions[event_id] for event_id in event_ids]


store = InMemoryStore()
