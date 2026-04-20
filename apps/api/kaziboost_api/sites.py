from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import HTMLResponse

from .auth import get_current_user_and_tenant
from .models import PageCreateRequest, PageOut, PublishResponse, SEOAssetLinks, SiteCreateRequest, SiteOut
from .store import Tenant, User, store


router = APIRouter(prefix="/v1/sites", tags=["sites"])


def _site_out(site) -> SiteOut:
    return SiteOut(
        id=site.id,
        name=site.name,
        template_key=site.template_key,
        primary_language=site.primary_language,
        status=site.status,
        published_url=site.published_url,
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


@router.post("", response_model=SiteOut, status_code=status.HTTP_201_CREATED)
def create_site(payload: SiteCreateRequest, current: tuple[User, Tenant] = Depends(get_current_user_and_tenant)) -> SiteOut:
    user, _ = current
    site = store.create_site(
        tenant_id=user.tenant_id,
        name=payload.name,
        template_key=payload.template_key,
        primary_language=payload.primary_language,
    )
    return _site_out(site)


@router.post("/{site_id}/pages", response_model=PageOut, status_code=status.HTTP_201_CREATED)
def add_page(
    site_id: str,
    payload: PageCreateRequest,
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
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


@router.post("/{site_id}/publish", response_model=PublishResponse)
def publish_site(site_id: str, current: tuple[User, Tenant] = Depends(get_current_user_and_tenant)) -> PublishResponse:
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


@router.get("/{site_id}/pages/{slug}/render", response_class=HTMLResponse)
def render_page(
    site_id: str,
    slug: str,
    device: str = Query(default="mobile"),
    current: tuple[User, Tenant] = Depends(get_current_user_and_tenant),
) -> HTMLResponse:
    user, _ = current
    try:
        site = store.get_site(tenant_id=user.tenant_id, site_id=site_id)
        page = store.get_page_by_slug(tenant_id=user.tenant_id, site_id=site_id, slug=slug)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    viewport = '<meta name="viewport" content="width=device-width, initial-scale=1" />'
    if device != "mobile":
        viewport = '<meta name="viewport" content="width=device-width, initial-scale=1" />'

    html = (
        "<!doctype html>"
        f"<html lang=\"{page.language}\">"
        "<head>"
        f"<title>{page.title}</title>"
        f"{viewport}"
        f"<meta name=\"description\" content=\"{site.name} - {page.title}\" />"
        "</head>"
        f"<body><h1>{page.title}</h1><p>Template: {site.template_key}</p></body>"
        "</html>"
    )
    return HTMLResponse(content=html)
