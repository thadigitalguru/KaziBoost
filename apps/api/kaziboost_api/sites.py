from html import escape
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import HTMLResponse

from .auth import SITE_ADMIN_ROLES, SITE_CONTENT_ROLES, get_current_user_and_tenant, require_roles
from .models import (
    HreflangItem,
    HreflangMapResponse,
    PageCreateRequest,
    PageListResponse,
    PageOut,
    PublishResponse,
    SEOAssetLinks,
    SiteCreateRequest,
    SiteDomainRequest,
    SiteDomainResponse,
    SiteOut,
    SiteStatusResponse,
    SiteTemplateItem,
    SiteTemplateListResponse,
    SiteListResponse,
)
from .store import Tenant, User, store


router = APIRouter(prefix="/v1/sites", tags=["sites"])


def _html(value: str) -> str:
    return escape(value, quote=True)


def _path_part(value: str) -> str:
    return quote(value, safe="")


def _page_path(slug: str) -> str:
    if slug == "home":
        return "/"
    return f"/{_path_part(slug)}"


def _published_page_href(published_url: str, slug: str, language: str) -> str:
    return f"{published_url}{_page_path(slug)}?language={_path_part(language)}"


@router.get("/templates", response_model=SiteTemplateListResponse)
def list_templates() -> SiteTemplateListResponse:
    items = [SiteTemplateItem(**item) for item in store.list_site_templates()]
    return SiteTemplateListResponse(total=len(items), items=items)


def _site_out(site) -> SiteOut:
    return SiteOut(
        id=site.id,
        name=site.name,
        template_key=site.template_key,
        primary_language=site.primary_language,
        status=site.status,
        published_url=site.published_url,
        custom_domain=site.custom_domain,
    )


def _page_out(page) -> PageOut:
    return PageOut(
        id=page.id,
        site_id=page.site_id,
        slug=page.slug,
        title=page.title,
        language=page.language,
        body_blocks=page.body_blocks,
    )


@router.get("", response_model=SiteListResponse)
def list_sites(
    status: str | None = Query(default=None),
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> SiteListResponse:
    user, _ = current
    items = [_site_out(site) for site in store.list_sites(tenant_id=user.tenant_id, status=status)]
    return SiteListResponse(total=len(items), items=items)


@router.get("/{site_id}", response_model=SiteOut)
def get_site(site_id: str, current: tuple[User, Tenant] = Depends(get_current_user_and_tenant)) -> SiteOut:
    user, _ = current
    try:
        site = store.get_site(tenant_id=user.tenant_id, site_id=site_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _site_out(site)


@router.post("", response_model=SiteOut, status_code=status.HTTP_201_CREATED)
def create_site(
    payload: SiteCreateRequest,
    current: tuple[User, Tenant] = Depends(require_roles(*SITE_CONTENT_ROLES)),
) -> SiteOut:
    user, _ = current
    site = store.create_site(
        tenant_id=user.tenant_id,
        name=payload.name,
        template_key=payload.template_key,
        primary_language=payload.primary_language,
    )
    return _site_out(site)


@router.get("/{site_id}/pages", response_model=PageListResponse)
def list_pages(
    site_id: str,
    language: str | None = Query(default=None),
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> PageListResponse:
    user, _ = current
    try:
        items = store.list_site_pages(tenant_id=user.tenant_id, site_id=site_id, language=language)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    pages = [_page_out(page) for page in items]
    return PageListResponse(total=len(pages), items=pages)


@router.get("/{site_id}/pages/{page_id}", response_model=PageOut)
def get_page(
    site_id: str,
    page_id: str,
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> PageOut:
    user, _ = current
    try:
        page = store.get_site_page(tenant_id=user.tenant_id, site_id=site_id, page_id=page_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _page_out(page)


@router.post("/{site_id}/pages", response_model=PageOut, status_code=status.HTTP_201_CREATED)
def add_page(
    site_id: str,
    payload: PageCreateRequest,
    current: tuple[User, Tenant] = Depends(require_roles(*SITE_CONTENT_ROLES)),
) -> PageOut:
    user, _ = current
    try:
        page = store.add_page(
            tenant_id=user.tenant_id,
            site_id=site_id,
            slug=payload.slug,
            title=payload.title,
            language=payload.language,
            body_blocks=payload.body_blocks,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _page_out(page)


@router.post("/{site_id}/domain", response_model=SiteDomainResponse)
def attach_domain(
    site_id: str,
    payload: SiteDomainRequest,
    current: tuple[User, Tenant] = Depends(require_roles(*SITE_ADMIN_ROLES)),
) -> SiteDomainResponse:
    user, _ = current
    try:
        site = store.create_site_domain(tenant_id=user.tenant_id, site_id=site_id, domain=payload.domain)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return SiteDomainResponse(site_id=site.id, domain=site.custom_domain or "", status="connected")


@router.post("/{site_id}/publish", response_model=PublishResponse)
def publish_site(
    site_id: str,
    current: tuple[User, Tenant] = Depends(require_roles(*SITE_CONTENT_ROLES)),
) -> PublishResponse:
    user, _ = current
    try:
        site = store.publish_site(tenant_id=user.tenant_id, site_id=site_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return PublishResponse(
        site_id=site.id,
        status=site.status,
        published_url=site.published_url or "",
        seo_assets=SEOAssetLinks(
            sitemap_url=f"/v1/sites/{site.id}/seo/sitemap.xml",
            robots_url=f"/v1/sites/{site.id}/seo/robots.txt",
            localbusiness_schema_url=f"/v1/sites/{site.id}/seo/localbusiness-schema",
        ),
    )


@router.post("/{site_id}/unpublish", response_model=SiteStatusResponse)
def unpublish_site(
    site_id: str,
    current: tuple[User, Tenant] = Depends(require_roles(*SITE_CONTENT_ROLES)),
) -> SiteStatusResponse:
    user, _ = current
    try:
        site = store.unpublish_site(tenant_id=user.tenant_id, site_id=site_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return SiteStatusResponse(site_id=site.id, status=site.status, published_url=site.published_url)


@router.delete("/{site_id}")
def delete_site(
    site_id: str,
    current: tuple[User, Tenant] = Depends(require_roles(*SITE_ADMIN_ROLES)),
) -> dict:
    user, _ = current
    try:
        store.delete_site(tenant_id=user.tenant_id, site_id=site_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return {"id": site_id, "status": "deleted"}


@router.get("/{site_id}/seo/sitemap.xml")
def sitemap(site_id: str, current: tuple[User, Tenant] = Depends(get_current_user_and_tenant)) -> Response:
    user, _ = current
    try:
        assets = store.get_seo_assets(tenant_id=user.tenant_id, site_id=site_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return Response(content=assets.sitemap_xml, media_type="application/xml")


@router.get("/{site_id}/seo/robots.txt")
def robots(site_id: str, current: tuple[User, Tenant] = Depends(get_current_user_and_tenant)) -> Response:
    user, _ = current
    try:
        assets = store.get_seo_assets(tenant_id=user.tenant_id, site_id=site_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return Response(content=assets.robots_txt, media_type="text/plain")


@router.get("/{site_id}/seo/localbusiness-schema")
def localbusiness_schema(site_id: str, current: tuple[User, Tenant] = Depends(get_current_user_and_tenant)) -> dict:
    user, _ = current
    try:
        assets = store.get_seo_assets(tenant_id=user.tenant_id, site_id=site_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return assets.localbusiness_schema


@router.get("/{site_id}/seo/hreflang-map", response_model=HreflangMapResponse)
def hreflang_map(site_id: str, current: tuple[User, Tenant] = Depends(get_current_user_and_tenant)) -> HreflangMapResponse:
    user, _ = current
    try:
        items = store.hreflang_map(tenant_id=user.tenant_id, site_id=site_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return HreflangMapResponse(total=len(items), items=[HreflangItem(**item) for item in items])


@router.get("/{site_id}/pages/{slug}/render", response_class=HTMLResponse)
def render_page(
    site_id: str,
    slug: str,
    device: str = Query(default="mobile"),
    language: str | None = Query(default=None),
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> HTMLResponse:
    user, _ = current
    try:
        site = store.get_site(tenant_id=user.tenant_id, site_id=site_id)
        page = store.get_page_by_slug(tenant_id=user.tenant_id, site_id=site_id, slug=slug, language=language)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    viewport = '<meta name="viewport" content="width=device-width, initial-scale=1" />'
    if device != "mobile":
        viewport = '<meta name="viewport" content="width=device-width, initial-scale=1" />'

    hreflang_items = []
    if site.published_url:
        hreflang_items = [
            item for item in store.hreflang_map(tenant_id=user.tenant_id, site_id=site_id) if item["slug"] == slug
        ]
    alternate_links = ""
    if site.published_url:
        alternate_links = "".join(
            (
                f'<link rel="alternate" hreflang="{_html(item["language"])}" '
                f'href="{_html(_published_page_href(site.published_url, item["slug"], item["language"]))}" />'
            )
            for item in hreflang_items
        )
    language_switcher = ""
    if len(hreflang_items) > 1:
        links = "".join(
            (
                f'<a href="/v1/sites/{_path_part(site_id)}/pages/{_path_part(slug)}/render'
                f'?language={_path_part(item["language"])}">{_html(item["language"])}</a>'
            )
            for item in hreflang_items
        )
        language_switcher = f'<nav data-language-switcher="true">{links}</nav>'

    html = (
        "<!doctype html>"
        f"<html lang=\"{_html(page.language)}\">"
        "<head>"
        f"<title>{_html(page.title)}</title>"
        f"{viewport}"
        f"<meta name=\"description\" content=\"{_html(site.name)} - {_html(page.title)}\" />"
        f"{alternate_links}"
        "</head>"
        f"<body>{language_switcher}<h1>{_html(page.title)}</h1><p>Template: {_html(site.template_key)}</p></body>"
        "</html>"
    )
    return HTMLResponse(content=html)
