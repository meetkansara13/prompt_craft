"""
app/core/frameworks/registry.py
=================================
All supported prompt frameworks as structured Python objects.
The FrameworkRegistry is the single source of truth — no magic strings.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Framework:
    key: str
    name: str
    full_name: str
    components: list[str]
    tier: str           # expert | advanced | simple | reasoning | gemini
    description: str
    best_for: str


FRAMEWORKS: list[Framework] = [
    Framework(
        key="RISEN",
        name="RISEN",
        full_name="Role · Instructions · Steps · End Goal · Narrowing",
        components=["Role", "Instructions", "Steps", "End Goal", "Narrowing"],
        tier="expert",
        description="The most complete framework for complex professional tasks.",
        best_for="Content creation, analysis, multi-step business tasks",
    ),
    Framework(
        key="COAST",
        name="COAST",
        full_name="Context · Objective · Actions · Scenario · Task",
        components=["Context", "Objective", "Actions", "Scenario", "Task"],
        tier="expert",
        description="Scenario-first framework excellent for situational tasks.",
        best_for="Customer service, roleplay, situation-based tasks",
    ),
    Framework(
        key="BROKE",
        name="BROKE",
        full_name="Background · Role · Objectives · Key results · Evolve",
        components=["Background", "Role", "Objectives", "Key Results", "Evolve"],
        tier="expert",
        description="Results-oriented framework with iteration built in.",
        best_for="Strategy, OKRs, product planning, iterative work",
    ),
    Framework(
        key="ROSES",
        name="ROSES",
        full_name="Role · Objective · Scenario · Expected Solution · Steps",
        components=["Role", "Objective", "Scenario", "Expected Solution", "Steps"],
        tier="expert",
        description="Solution-first framework that defines the expected output upfront.",
        best_for="Technical problem solving, engineering, precise deliverables",
    ),
    Framework(
        key="CARE",
        name="CARE",
        full_name="Context · Action · Result · Example",
        components=["Context", "Action", "Result", "Example"],
        tier="advanced",
        description="Example-driven framework that anchors output to concrete references.",
        best_for="Writing tasks, transformation tasks, style matching",
    ),
    Framework(
        key="RACE",
        name="RACE",
        full_name="Role · Action · Context · Expectation",
        components=["Role", "Action", "Context", "Expectation"],
        tier="advanced",
        description="Expectation-explicit framework that reduces ambiguity.",
        best_for="Professional writing, reports, structured deliverables",
    ),
    Framework(
        key="TRACE",
        name="TRACE",
        full_name="Task · Request · Action · Context · Example",
        components=["Task", "Request", "Action", "Context", "Example"],
        tier="advanced",
        description="Task-first with examples for consistent reproducible output.",
        best_for="Code generation, data tasks, template-based work",
    ),
    Framework(
        key="PTCF",
        name="PTCF",
        full_name="Persona · Task · Context · Format",
        components=["Persona", "Task", "Context", "Format"],
        tier="gemini",
        description="Gemini's native framework. Direct and efficient.",
        best_for="Gemini AI, quick structured prompts",
    ),
    Framework(
        key="RTF",
        name="RTF",
        full_name="Role · Task · Format",
        components=["Role", "Task", "Format"],
        tier="simple",
        description="Minimal 3-part framework. Fast and clean.",
        best_for="Simple tasks, API calls, quick prompts",
    ),
    Framework(
        key="APE",
        name="APE",
        full_name="Action · Purpose · Expectation",
        components=["Action", "Purpose", "Expectation"],
        tier="simple",
        description="Purpose-driven minimal framework.",
        best_for="Short prompts, clear single-task requests",
    ),
    Framework(
        key="chain",
        name="Chain Prompt",
        full_name="Multi-step chained prompts",
        components=["Step 1", "Step 2", "Step N", "Synthesis"],
        tier="reasoning",
        description="Breaks complex tasks into sequential chained sub-prompts.",
        best_for="Complex reasoning, multi-stage research, long outputs",
    ),
]

# Fast lookup by key
FRAMEWORK_REGISTRY: dict[str, Framework] = {f.key: f for f in FRAMEWORKS}


def get_framework(key: str) -> Framework:
    if key not in FRAMEWORK_REGISTRY:
        raise KeyError(f"Unknown framework: {key}. Available: {list(FRAMEWORK_REGISTRY.keys())}")
    return FRAMEWORK_REGISTRY[key]


def all_frameworks() -> list[Framework]:
    return FRAMEWORKS
