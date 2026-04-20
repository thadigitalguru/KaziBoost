from pydantic import BaseModel, EmailStr, Field


class SignUpRequest(BaseModel):
    business_name: str = Field(min_length=2, max_length=120)
    owner_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TenantOut(BaseModel):
    id: str
    name: str


class UserOut(BaseModel):
    id: str
    tenant_id: str
    owner_name: str
    email: EmailStr
    role: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
    tenant: TenantOut


class SignUpResponse(BaseModel):
    user: UserOut
    tenant: TenantOut


class SiteCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    template_key: str = Field(min_length=2, max_length=80)
    primary_language: str = Field(min_length=2, max_length=10)


class SiteOut(BaseModel):
    id: str
    name: str
    template_key: str
    primary_language: str
    status: str
    published_url: str | None = None


class PageCreateRequest(BaseModel):
    slug: str = Field(min_length=1, max_length=80)
    title: str = Field(min_length=2, max_length=140)
    language: str = Field(min_length=2, max_length=10)
    body_blocks: list[str] = Field(default_factory=list)


class PageOut(BaseModel):
    id: str
    site_id: str
    slug: str
    title: str
    language: str
    body_blocks: list[str]


class SEOAssetLinks(BaseModel):
    sitemap_url: str
    robots_url: str
    localbusiness_schema_url: str


class PublishResponse(BaseModel):
    site_id: str
    status: str
    published_url: str
    seo_assets: SEOAssetLinks


class CRMFormCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    kind: str = Field(min_length=2, max_length=40)
    fields: list[str] = Field(default_factory=list)


class CRMFormOut(BaseModel):
    id: str
    name: str
    kind: str
    fields: list[str]


class LeadSubmitRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    phone: str = Field(min_length=7, max_length=30)
    email: EmailStr
    message: str = Field(min_length=1, max_length=500)
    source: str = Field(min_length=2, max_length=40)
    tags: list[str] = Field(default_factory=list)


class ContactOut(BaseModel):
    id: str
    name: str
    phone: str
    email: EmailStr
    source: str
    tags: list[str]


class LeadSubmissionOut(BaseModel):
    id: str
    form_id: str
    source: str
    message: str
    contact: ContactOut


class ContactListResponse(BaseModel):
    total: int
    items: list[ContactOut]


class KeywordSuggestRequest(BaseModel):
    seed_query: str = Field(min_length=2, max_length=120)
    location: str = Field(min_length=2, max_length=80)
    language: str = Field(default="en", min_length=2, max_length=10)


class KeywordItem(BaseModel):
    keyword: str
    intent: str
    volume_band: str


class KeywordSuggestResponse(BaseModel):
    total: int
    items: list[KeywordItem]


class SaveKeywordsRequest(BaseModel):
    workspace: str = Field(min_length=2, max_length=80)
    keywords: list[str] = Field(default_factory=list)


class GenerateContentRequest(BaseModel):
    keyword: str = Field(min_length=2, max_length=120)
    content_type: str = Field(default="blog", min_length=2, max_length=40)
    tone: str = Field(default="conversational", min_length=2, max_length=40)
    language: str = Field(default="en", min_length=2, max_length=10)
    length: str = Field(default="medium", min_length=2, max_length=20)


class GenerateContentResponse(BaseModel):
    keyword: str
    language: str
    title: str
    meta_title: str
    meta_description: str
    body: str
    related_terms: list[str]


class WhatsAppIncomingRequest(BaseModel):
    from_phone: str = Field(min_length=7, max_length=30)
    message_text: str = Field(min_length=1, max_length=1000)
    language: str = Field(default="en", min_length=2, max_length=10)


class WhatsAppConversationOut(BaseModel):
    thread_id: str
    from_phone: str
    status: str
    last_message: str
    assigned_to: str | None = None


class WhatsAppConversationListResponse(BaseModel):
    total: int
    items: list[WhatsAppConversationOut]


class WhatsAppFAQCreateRequest(BaseModel):
    question: str = Field(min_length=2, max_length=300)
    answer: str = Field(min_length=2, max_length=500)


class WhatsAppBotReplyResponse(BaseModel):
    mode: str
    reply_text: str
    thread_id: str


class WhatsAppHandoffRequest(BaseModel):
    assigned_to: str = Field(min_length=2, max_length=80)
