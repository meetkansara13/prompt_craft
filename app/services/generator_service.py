"""
app/services/generator_service.py
====================================
GeneratorService orchestrates the full prompt generation flow:

  1. Receive a validated GenerateRequest
  2. Ask PromptEngine to build the system prompt (pure Python logic)
  3. Ask AnthropicClient to call Claude
  4. Parse JSON response and validate against GenerateResponse model
  5. Return typed GenerateResponse

The route handler only needs to call one method and handle the result.
No AI-specific code lives in routes.
"""

from app.core.engines.prompt_engine import PromptEngine
from app.models.prompt_models import GenerateRequest, GenerateResponse, RefineRequest, RefineResponse
from app.services.anthropic_client import AnthropicClient
from app.utils.json_parser import extract_json
from app.utils.errors import JSONParseError
from app.utils.logger import get_logger

logger = get_logger(__name__)


class GeneratorService:
    """
    Coordinates: PromptEngine → AnthropicClient → JSON parsing → Pydantic validation.
    One service instance is created per request (stateless).
    """

    def __init__(self, api_key: str) -> None:
        self._engine = PromptEngine()
        self._client = AnthropicClient(api_key=api_key)

    def generate(self, req: GenerateRequest) -> dict:
        """
        Full generation flow.

        Returns
        -------
        dict : Validated GenerateResponse as a plain dict (for JSON serialisation)
        """
        logger.info(
            "GeneratorService.generate | model=%s framework=%s goal_len=%d",
            req.model, req.framework, len(req.goal),
        )

        # 1. Build system prompt from Python data
        system_prompt = self._engine.build_system_prompt(
            framework_key=req.framework,
            target_model=req.model,
            selected_cheat_keys=req.cheat_codes,
            selected_techniques=req.techniques,
        )

        # 2. Build user message
        user_message = self._engine.build_user_message(
            goal=req.goal,
            model=req.model,
            category=req.category,
            output_format=req.output_format,
            complexity=req.complexity,
            tones=req.tones,
            framework_key=req.framework,
            techniques=req.techniques,
            cheat_codes=req.cheat_codes,
        )

        # 3. Call Claude
        raw_text = self._client.complete(system=system_prompt, user=user_message)

        # 4. Parse JSON safely
        data = extract_json(raw_text)

        # 5. Validate and return
        try:
            response = GenerateResponse(**data)
            logger.info(
                "Generation complete | score=%s grade=%s",
                data.get("quality_score", {}).get("score"),
                data.get("quality_score", {}).get("grade"),
            )
            return response.model_dump()
        except Exception as exc:
            logger.warning("Pydantic validation failed, returning raw data: %s", exc)
            # Return raw data rather than failing — Claude sometimes omits optional fields
            return data

    def refine(self, req: RefineRequest) -> dict:
        """
        Refinement flow — takes existing prompt + feedback, returns improved version.
        """
        logger.info(
            "GeneratorService.refine | prompt_len=%d feedback_len=%d",
            len(req.current_prompt), len(req.feedback),
        )

        system_prompt = self._engine.build_refine_system_prompt()

        user_message = (
            f"CURRENT PROMPT:\n---\n{req.current_prompt}\n---\n\n"
            f"USER FEEDBACK:\n{req.feedback}\n\n"
            "Apply this feedback precisely. Produce an improved version. "
            "Fill all JSON fields."
        )

        raw_text = self._client.complete(system=system_prompt, user=user_message)
        data = extract_json(raw_text)

        try:
            response = RefineResponse(**data)
            return response.model_dump()
        except Exception as exc:
            logger.warning("Pydantic validation on refine failed: %s", exc)
            return data
