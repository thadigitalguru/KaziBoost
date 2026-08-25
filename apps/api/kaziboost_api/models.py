from pydantic import BaseModel, EmailStr, Field


class ErrorResponse(BaseModel):
    detail: str | list[dict] | dict
    code: str
    request_id: str | None = None


class HealthResponse(BaseModel):
    status: str


class ReadinessResponse(BaseModel):
    status: str
    checks: dict[str, str]


class SignUpRequest(BaseModel):
    business_name: str = Field(min_length=2, max_length=120)
    owner_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class CreateTeammateRequest(BaseModel):
    owner_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8)
    role: str = Field(min_length=2, max_length=30)


class UpdateRoleRequest(BaseModel):
    role: str = Field(min_length=2, max_length=30)


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


class TenantSettingsRequest(BaseModel):
    business_name: str = Field(min_length=2, max_length=120)
    owner_name: str = Field(min_length=2, max_length=120)


class TenantSettingsResponse(BaseModel):
    tenant: TenantOut
    user: UserOut


class SupportFeedbackRequest(BaseModel):
    page: str = Field(min_length=1, max_length=120)
    message: str = Field(min_length=10, max_length=1000)


class SupportFeedbackResponse(BaseModel):
    status: str
    feedback_id: str


class MFAEnrollResponse(BaseModel):
    enabled: bool
    secret: str
    backup_codes: list[str]


class MFAChallengeResponse(BaseModel):
    challenge_id: str
    status: str
    test_code: str


class MFAVerifyRequest(BaseModel):
    challenge_id: str
    code: str = Field(min_length=4, max_length=20)


class MFAVerifyResponse(BaseModel):
    challenge_id: str
    status: str


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
    custom_domain: str | None = None


class SiteDomainRequest(BaseModel):
    domain: str = Field(min_length=4, max_length=255)


class SiteDomainResponse(BaseModel):
    site_id: str
    domain: str
    status: str


class SiteStatusResponse(BaseModel):
    site_id: str
    status: str
    published_url: str | None = None


class SiteTemplateItem(BaseModel):
    key: str
    name: str
    category: str
    primary_language: str


class SiteTemplateListResponse(BaseModel):
    total: int
    items: list[SiteTemplateItem]


class SiteListResponse(BaseModel):
    total: int
    items: list[SiteOut]


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


class PageListResponse(BaseModel):
    total: int
    items: list[PageOut]


class WorkspaceRenameRequest(BaseModel):
    new_workspace: str = Field(min_length=2, max_length=80)


class SEOAssetLinks(BaseModel):
    sitemap_url: str
    robots_url: str
    localbusiness_schema_url: str


class PublishResponse(BaseModel):
    site_id: str
    status: str
    published_url: str
    seo_assets: SEOAssetLinks


class HreflangItem(BaseModel):
    language: str
    slug: str
    href: str


class HreflangMapResponse(BaseModel):
    total: int
    items: list[HreflangItem]


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
    email: str
    source: str
    tags: list[str]
    consent: dict[str, bool] = Field(default_factory=dict)


class LeadSubmissionOut(BaseModel):
    id: str
    form_id: str
    source: str
    message: str
    contact: ContactOut


class ContactTimelineEvent(BaseModel):
    id: str
    type: str
    source: str
    message: str
    form_id: str
    created_at: str


class ContactListResponse(BaseModel):
    total: int
    items: list[ContactOut]
    limit: int | None = None
    offset: int = 0


class ContactSearchResponse(BaseModel):
    total: int
    items: list[ContactOut]


class ContactTimelineResponse(BaseModel):
    events: list[ContactTimelineEvent]


class ContactNoteCreateRequest(BaseModel):
    text: str = Field(min_length=2, max_length=1000)


class ContactNoteOut(BaseModel):
    id: str
    contact_id: str
    text: str
    created_at: str


class ContactNoteListResponse(BaseModel):
    total: int
    items: list[ContactNoteOut]


class ContactConsentUpdateRequest(BaseModel):
    email_marketing: bool
    sms_marketing: bool


class ContactTagsUpdateRequest(BaseModel):
    tags: list[str] = Field(default_factory=list)


class ContactExportResponse(BaseModel):
    contact: ContactOut
    timeline: list[ContactTimelineEvent]


class SegmentCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    tag: str | None = None
    source: str | None = None


class SegmentUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    tag: str | None = None
    source: str | None = None


class SegmentOut(BaseModel):
    id: str
    name: str
    tag: str | None = None
    source: str | None = None


class SegmentDetailResponse(BaseModel):
    id: str
    name: str
    tag: str | None = None
    source: str | None = None
    contact_count: int


class SegmentListResponse(BaseModel):
    total: int
    items: list[SegmentOut]


class CampaignSendRequest(BaseModel):
    channel: str = Field(min_length=3, max_length=20)
    subject: str = Field(min_length=2, max_length=200)
    message: str = Field(min_length=2, max_length=2000)
    tag: str | None = None
    source: str | None = None


class CampaignSendResponse(BaseModel):
    id: str
    channel: str
    subject: str
    recipients: int


class CampaignHistoryItem(BaseModel):
    id: str
    channel: str
    subject: str
    recipients: int
    created_at: str


class CampaignHistoryResponse(BaseModel):
    total: int
    items: list[CampaignHistoryItem]


class CampaignStatsResponse(BaseModel):
    total_campaigns: int
    total_recipients: int
    by_channel: dict[str, int]


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


class GeneratedContentOut(BaseModel):
    id: str
    keyword: str
    content_type: str
    tone: str
    language: str
    length: str
    title: str
    meta_title: str
    meta_description: str
    body: str
    related_terms: list[str]
    prompt_version: str
    generation_mode: str
    safety_outcome: str
    policy_violations: list[str]
    status: str
    reviewed_by: str | None = None
    reviewed_at: str | None = None
    review_note: str | None = None
    created_at: str | None = None


class GenerateContentResponse(BaseModel):
    id: str
    keyword: str
    language: str
    title: str
    meta_title: str
    meta_description: str
    body: str
    related_terms: list[str]
    prompt_version: str
    generation_mode: str
    safety_outcome: str
    policy_violations: list[str]


class ContentHistoryResponse(BaseModel):
    total: int
    items: list[GeneratedContentOut]


class ContentReviewRequest(BaseModel):
    status: str = Field(min_length=7, max_length=20)
    review_note: str | None = Field(default=None, max_length=500)


class SaveKeywordsResponse(BaseModel):
    workspace: str
    count: int
    keywords: list[str]


class KeywordWorkspaceItem(BaseModel):
    workspace: str
    count: int


class KeywordWorkspaceListResponse(BaseModel):
    total: int
    items: list[KeywordWorkspaceItem]


class TopicMapGenerateRequest(BaseModel):
    seed_keyword: str = Field(min_length=2, max_length=120)
    location: str = Field(min_length=2, max_length=80)
    language: str = Field(default="en", min_length=2, max_length=10)


class TopicMapInternalLink(BaseModel):
    from_: str = Field(alias="from")
    to: str
    anchor_text: str


class TopicMapResponse(BaseModel):
    pillar_topic: str
    cluster_topics: list[str]
    internal_links: list[dict[str, str]]


class ContentCalendarCreateRequest(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    keyword: str = Field(min_length=2, max_length=120)
    scheduled_for: str
    language: str = Field(default="en", min_length=2, max_length=10)
    generated_content_id: str | None = None


class ContentCalendarItemOut(BaseModel):
    id: str
    title: str
    keyword: str
    scheduled_for: str
    language: str
    status: str
    generated_content_id: str | None = None


class ContentCalendarListResponse(BaseModel):
    total: int
    items: list[ContentCalendarItemOut]
    limit: int | None = None
    offset: int = 0


class ContentCalendarStatusUpdateRequest(BaseModel):
    status: str = Field(min_length=4, max_length=20)


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
    idempotent: bool = False


class WhatsAppConversationListResponse(BaseModel):
    total: int
    items: list[WhatsAppConversationOut]
    limit: int | None = None
    offset: int = 0


class WhatsAppReminderRequest(BaseModel):
    message: str = Field(min_length=3, max_length=500)


class WhatsAppReminderOut(BaseModel):
    id: str
    thread_id: str
    message: str
    status: str
    created_at: str


class WhatsAppReminderListResponse(BaseModel):
    total: int
    items: list[WhatsAppReminderOut]
    limit: int | None = None
    offset: int = 0


class WhatsAppFAQCreateRequest(BaseModel):
    question: str = Field(min_length=2, max_length=300)
    answer: str = Field(min_length=2, max_length=500)


class WhatsAppBotReplyResponse(BaseModel):
    mode: str
    reply_text: str
    thread_id: str


class WhatsAppHandoffRequest(BaseModel):
    assigned_to: str = Field(min_length=2, max_length=80)


class WhatsAppHumanReplyRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)


class WhatsAppHumanReplyResponse(BaseModel):
    thread_id: str
    message: str
    sent_by: str
    status: str


class MpesaInitiateRequest(BaseModel):
    phone: str = Field(min_length=7, max_length=30)
    amount: int = Field(ge=1)
    currency: str = Field(default="KES", min_length=3, max_length=3)
    reference: str = Field(min_length=2, max_length=80)
    contact_id: str | None = None


class PaymentOut(BaseModel):
    payment_id: str
    provider: str
    phone: str
    amount: int
    currency: str
    reference: str
    status: str
    contact_id: str | None = None
    provider_tx_id: str | None = None
    reason: str | None = None


class MpesaCallbackRequest(BaseModel):
    payment_id: str
    provider_tx_id: str
    status: str
    reason: str | None = None


class ReportScheduleRequest(BaseModel):
    email: EmailStr
    frequency: str = Field(default="weekly", min_length=4, max_length=20)


class ReportScheduleResponse(BaseModel):
    id: str
    email: EmailStr
    frequency: str
    status: str


class ReportScheduleListResponse(BaseModel):
    total: int
    items: list[ReportScheduleResponse]


class ReportScheduleUpdateRequest(BaseModel):
    frequency: str = Field(min_length=4, max_length=20)


class AnalyticsConnectorRequest(BaseModel):
    provider: str = Field(min_length=2, max_length=40)
    property_id: str = Field(min_length=2, max_length=120)
    status: str = Field(default="connected", min_length=4, max_length=20)


class AnalyticsConnectorResponse(BaseModel):
    id: str
    provider: str
    property_id: str
    status: str


class AnalyticsConnectorListResponse(BaseModel):
    total: int
    items: list[AnalyticsConnectorResponse]


class AnalyticsConnectorUpdateRequest(BaseModel):
    status: str = Field(min_length=4, max_length=20)


class AnalyticsKpis(BaseModel):
    total_leads: int
    open_conversations: int
    successful_payments: int
    published_sites: int


class AnalyticsDashboardResponse(BaseModel):
    kpis: AnalyticsKpis


class AnalyticsDashboardSummaryResponse(BaseModel):
    kpis: AnalyticsKpis
    trend: dict[str, object]


class AnalyticsFunnelResponse(BaseModel):
    stages: dict[str, int]
    conversion: dict[str, float]


class MpesaCallbackResponse(BaseModel):
    payment_id: str
    idempotent: bool
    status: str


class PaymentListResponse(BaseModel):
    total: int
    items: list[PaymentOut]
    limit: int | None = None
    offset: int = 0


class PaymentReconciliationSummaryResponse(BaseModel):
    contact_id: str
    total: int
    by_status: dict[str, int]
    total_amount: int


class RefundRequest(BaseModel):
    amount: int = Field(ge=1)
    reason: str = Field(min_length=2, max_length=120)


class RefundOut(BaseModel):
    refund_id: str
    payment_id: str
    amount: int
    reason: str
    status: str


class RefundListResponse(BaseModel):
    total: int
    items: list[RefundOut]
    limit: int | None = None
    offset: int = 0


class PaymentsSummaryResponse(BaseModel):
    totals: dict[str, int]
    by_status: dict[str, dict[str, int]]


class PaymentsMonthlyReportResponse(BaseModel):
    month: str
    successful_count: int
    successful_revenue: int


class RefundReportResponse(BaseModel):
    total_refunds: int
    by_reason: dict[str, dict[str, int]]


class PaymentFailureItem(BaseModel):
    payment_id: str
    provider_tx_id: str | None = None
    reason: str | None = None
    amount: int


class PaymentFailureListResponse(BaseModel):
    total: int
    items: list[PaymentFailureItem]
    limit: int | None = None
    offset: int = 0


class PaymentProviderRequest(BaseModel):
    provider: str = Field(min_length=2, max_length=40)
    channel: str = Field(min_length=2, max_length=40)
    status: str = Field(default="active", min_length=3, max_length=20)


class PaymentProviderResponse(BaseModel):
    id: str
    provider: str
    channel: str
    status: str


class PaymentProviderListResponse(BaseModel):
    total: int
    items: list[PaymentProviderResponse]


class PaymentProviderUpdateRequest(BaseModel):
    status: str = Field(min_length=3, max_length=20)


class AuditEventOut(BaseModel):
    id: str
    event_type: str
    actor_user_id: str | None = None
    entity_type: str
    entity_id: str
    metadata: dict[str, str]
    created_at: str


class AuditEventListResponse(BaseModel):
    total: int
    items: list[AuditEventOut]


class OnboardingChecklistResponse(BaseModel):
    completed: int
    total: int
    items: dict[str, bool]


class OnboardingRecommendationsResponse(BaseModel):
    total: int
    items: list[dict[str, str]]


class TrainingArticleCreateRequest(BaseModel):
    title: str = Field(min_length=4, max_length=200)
    content: str = Field(min_length=10, max_length=5000)
    category: str = Field(min_length=2, max_length=80)


class TrainingArticleOut(BaseModel):
    id: str
    title: str
    content: str
    category: str
    featured: bool = False
    views: int = 0


class TrainingArticleListResponse(BaseModel):
    total: int
    items: list[TrainingArticleOut]
    limit: int | None = None
    offset: int = 0


class TrainingSearchResponse(BaseModel):
    total: int
    items: list[TrainingArticleOut]
    limit: int | None = None
    offset: int = 0


class TrainingArticleUpdateRequest(BaseModel):
    title: str | None = None
    content: str | None = None
    category: str | None = None
    featured: bool | None = None


class TrainingCategoryListResponse(BaseModel):
    total: int
    items: list[str]
