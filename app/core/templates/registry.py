"""
app/core/templates/registry.py
================================
20+ pre-built use case templates.
Each template pre-fills the goal, recommends framework,
sets best techniques, and gives the user a head start.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class UseCaseTemplate:
    key: str
    icon: str
    label: str
    category: str
    goal: str
    framework: str
    techniques: list
    model: str = "claude"
    complexity: str = "moderate"
    tones: list = field(default_factory=lambda: ["professional"])


TEMPLATES: list[UseCaseTemplate] = [
    UseCaseTemplate(
        key="professional_email",
        icon="✉️",
        label="Professional Email",
        category="writing",
        goal="Write a professional email to [recipient] about [topic]. The email should [desired outcome]. Tone: formal but warm. Include a clear subject line and call to action.",
        framework="RISEN",
        techniques=["role", "selfcheck", "constraints"],
        tones=["professional"],
    ),
    UseCaseTemplate(
        key="code_review",
        icon="🔍",
        label="Code Review",
        category="coding",
        goal="Review the provided [Python/JavaScript/etc] code for security vulnerabilities, performance issues, code quality, and best practices. Output a structured report with severity levels.",
        framework="ROSES",
        techniques=["role", "fewshot", "selfcheck", "constraints", "xml"],
        model="claude",
        complexity="advanced",
        tones=["technical"],
    ),
    UseCaseTemplate(
        key="seo_blog",
        icon="📝",
        label="SEO Blog Post",
        category="writing",
        goal="Write a comprehensive SEO-optimized blog post about [topic] targeting the keyword '[keyword]'. Include introduction, 4-5 main sections with H2 headings, and conclusion. Target audience: [audience].",
        framework="COAST",
        techniques=["role", "cot", "constraints", "selfcheck"],
        tones=["professional", "friendly"],
    ),
    UseCaseTemplate(
        key="customer_support",
        icon="🎧",
        label="Customer Support Agent",
        category="conversation",
        goal="Create a customer support agent prompt for [company name] that handles [type of queries]. The agent should resolve issues efficiently, maintain brand voice, and escalate complex cases.",
        framework="RISEN",
        techniques=["role", "fewshot", "constraints", "selfcheck"],
        tones=["friendly", "professional"],
    ),
    UseCaseTemplate(
        key="product_description",
        icon="🛍️",
        label="Product Description",
        category="writing",
        goal="Write compelling product descriptions for [product name] targeting [audience]. Highlight key features, benefits, and unique selling points. Optimize for both humans and search engines.",
        framework="CARE",
        techniques=["role", "fewshot", "constraints"],
        tones=["persuasive", "professional"],
    ),
    UseCaseTemplate(
        key="data_analysis",
        icon="📊",
        label="Data Analysis",
        category="analysis",
        goal="Analyze the provided dataset about [topic]. Identify key trends, patterns, anomalies, and actionable insights. Present findings with supporting statistics and recommended next steps.",
        framework="ROSES",
        techniques=["role", "cot", "selfcheck", "constraints"],
        model="claude",
        complexity="advanced",
        tones=["technical", "professional"],
    ),
    UseCaseTemplate(
        key="resume_writer",
        icon="📄",
        label="Resume / CV Writer",
        category="writing",
        goal="Write a professional resume for a [job title] position with [years] years of experience in [industry]. Highlight achievements with quantified results. ATS-optimized.",
        framework="RISEN",
        techniques=["role", "fewshot", "constraints", "selfcheck"],
        tones=["professional"],
    ),
    UseCaseTemplate(
        key="sql_generator",
        icon="🗄️",
        label="SQL Query Generator",
        category="coding",
        goal="Generate optimized SQL queries for [database type] that [describe what queries should do]. Include proper indexing hints, handle edge cases, and add comments explaining complex logic.",
        framework="RTF",
        techniques=["role", "fewshot", "constraints", "selfcheck"],
        model="claude",
        complexity="advanced",
        tones=["technical"],
    ),
    UseCaseTemplate(
        key="api_docs",
        icon="📚",
        label="API Documentation",
        category="coding",
        goal="Write comprehensive API documentation for [API name]. Include endpoint descriptions, request/response examples, authentication, error codes, and code samples in [languages].",
        framework="ROSES",
        techniques=["role", "fewshot", "constraints"],
        tones=["technical"],
    ),
    UseCaseTemplate(
        key="unit_tests",
        icon="🧪",
        label="Unit Test Generator",
        category="coding",
        goal="Generate comprehensive unit tests for the provided [language] code. Cover happy path, edge cases, error cases, and boundary conditions. Use [testing framework].",
        framework="TRACE",
        techniques=["role", "fewshot", "constraints", "selfcheck"],
        model="claude",
        complexity="advanced",
        tones=["technical"],
    ),
    UseCaseTemplate(
        key="social_media",
        icon="📱",
        label="Social Media Content",
        category="writing",
        goal="Create engaging social media content for [platform] about [topic] for [brand/company]. Include [number] post variations with appropriate hashtags and calls to action.",
        framework="CARE",
        techniques=["role", "fewshot", "constraints"],
        tones=["creative", "friendly"],
    ),
    UseCaseTemplate(
        key="meeting_notes",
        icon="📋",
        label="Meeting Notes Summarizer",
        category="analysis",
        goal="Summarize the provided meeting transcript/notes into: key decisions made, action items with owners and deadlines, open questions, and next meeting agenda items.",
        framework="RTF",
        techniques=["role", "constraints", "selfcheck"],
        tones=["professional", "concise"],
    ),
    UseCaseTemplate(
        key="lesson_plan",
        icon="🎓",
        label="Lesson Plan Creator",
        category="education",
        goal="Create a detailed lesson plan for teaching [topic] to [age group/level] students. Include learning objectives, activities, assessments, and differentiation strategies. Duration: [time].",
        framework="ROSES",
        techniques=["role", "fewshot", "constraints", "selfcheck"],
        tones=["friendly", "professional"],
    ),
    UseCaseTemplate(
        key="competitor_analysis",
        icon="🔎",
        label="Competitor Analysis",
        category="business",
        goal="Conduct a comprehensive competitor analysis for [company] vs [competitors] in the [industry] market. Analyze: positioning, features, pricing, strengths, weaknesses, and opportunities.",
        framework="BROKE",
        techniques=["role", "cot", "constraints", "selfcheck"],
        model="claude",
        complexity="advanced",
        tones=["professional", "technical"],
    ),
    UseCaseTemplate(
        key="bug_report",
        icon="🐛",
        label="Bug Report Writer",
        category="coding",
        goal="Write a detailed bug report for [issue description]. Include steps to reproduce, expected vs actual behavior, environment details, severity assessment, and suggested fix if known.",
        framework="TRACE",
        techniques=["role", "fewshot", "constraints"],
        tones=["technical"],
    ),
    UseCaseTemplate(
        key="interview_questions",
        icon="💼",
        label="Interview Questions",
        category="business",
        goal="Generate comprehensive interview questions for a [job title] position. Include technical, behavioral, situational, and culture-fit questions. Add evaluation criteria for each question.",
        framework="RISEN",
        techniques=["role", "fewshot", "constraints"],
        tones=["professional"],
    ),
    UseCaseTemplate(
        key="brand_voice",
        icon="🎨",
        label="Brand Voice Guide",
        category="writing",
        goal="Create a comprehensive brand voice guide for [company name] in the [industry]. Define tone, vocabulary, writing style, dos and don'ts, and examples across different channels.",
        framework="COAST",
        techniques=["role", "fewshot", "constraints", "selfcheck"],
        tones=["creative", "professional"],
    ),
    UseCaseTemplate(
        key="ui_feedback",
        icon="🖥️",
        label="UI/UX Feedback",
        category="analysis",
        goal="Provide detailed UI/UX feedback for [product/page]. Evaluate: usability, accessibility, visual hierarchy, conversion optimization, and mobile responsiveness. Prioritize issues by impact.",
        framework="ROSES",
        techniques=["role", "fewshot", "constraints", "selfcheck"],
        tones=["technical", "professional"],
    ),
    UseCaseTemplate(
        key="legal_analyzer",
        icon="⚖️",
        label="Legal Document Analyzer",
        category="analysis",
        goal="Analyze the provided legal document for [purpose]. Identify: key terms and obligations, potential risks, unusual clauses, missing standard protections, and recommended clarifications.",
        framework="RISEN",
        techniques=["role", "constraints", "selfcheck"],
        model="claude",
        complexity="expert",
        tones=["professional", "technical"],
    ),
    UseCaseTemplate(
        key="agentic_workflow",
        icon="🤖",
        label="Agentic Workflow",
        category="agentic",
        goal="Design a multi-step agentic workflow for [task]. The agent should: [list main steps]. Handle errors gracefully, confirm before irreversible actions, and report progress at each stage.",
        framework="chain",
        techniques=["role", "react", "selfcheck", "constraints", "xml"],
        model="claude",
        complexity="expert",
        tones=["technical"],
    ),
]

# Fast lookup
TEMPLATE_REGISTRY: dict[str, UseCaseTemplate] = {t.key: t for t in TEMPLATES}


def get_template(key: str) -> UseCaseTemplate:
    if key not in TEMPLATE_REGISTRY:
        raise KeyError(f"Unknown template: {key}")
    return TEMPLATE_REGISTRY[key]


def all_templates() -> list[UseCaseTemplate]:
    return TEMPLATES


def templates_by_category() -> dict[str, list[UseCaseTemplate]]:
    result: dict[str, list[UseCaseTemplate]] = {}
    for t in TEMPLATES:
        result.setdefault(t.category, []).append(t)
    return result
