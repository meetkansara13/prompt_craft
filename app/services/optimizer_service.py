"""
app/services/optimizer_service.py
====================================
OptimizerService orchestrates the token optimization flow:

  1. Receive a validated OptimizeRequest
  2. Ask TokenEngine to build the system prompt (pure Python)
  3. Call Claude via AnthropicClient
  4. Parse and validate response
  5. Return typed OptimizeResponse dict
"""

from app.core.engines.token_engine import TokenEngine
from app.models.optimizer_models import OptimizeRequest, OptimizeResponse
from app.services.anthropic_client import AnthropicClient
from app.utils.json_parser import extract_json
from app.utils.logger import get_logger

logger = get_logger(__name__)


class OptimizerService:

    def __init__(self, api_key: str) -> None:
        self._engine = TokenEngine()
        self._client = AnthropicClient(api_key=api_key)

    def optimize(self, req: OptimizeRequest) -> dict:
        """
        Full optimization flow.

        Returns
        -------
        dict : Validated OptimizeResponse as a plain dict
        """
        original_token_estimate = TokenEngine.estimate_tokens(req.prompt)

        logger.info(
            "OptimizerService.optimize | model=%s level=%s tokens_est=%d",
            req.target_model, req.level, original_token_estimate,
        )

        # 1. Build prompts from Python engine
        system_prompt = self._engine.build_system_prompt()
        user_message  = self._engine.build_user_message(
            prompt=req.prompt,
            target_model=req.target_model,
            level=req.level,
            sensitivity=req.sensitivity,
            techniques=req.techniques,
            original_token_estimate=original_token_estimate,
        )

        # 2. Call Claude
        raw_text = self._client.complete(system=system_prompt, user=user_message)

        # 3. Parse JSON safely
        data = extract_json(raw_text)

        # 4. Validate
        try:
            response = OptimizeResponse(**data)
            logger.info(
                "Optimization complete | original=%s balanced=%s reduction=%s%%",
                data.get("analysis", {}).get("original_tokens"),
                data.get("versions", {}).get("balanced", {}).get("tokens"),
                data.get("versions", {}).get("balanced", {}).get("pct"),
            )
            return response.model_dump()
        except Exception as exc:
            logger.warning("Pydantic validation on optimize failed: %s", exc)
            return data
