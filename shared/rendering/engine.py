"""Unified Rendering Engine implementation.

Per ADR-0028: Unified Rendering Engine for Cross-Tool Visualization.

This module provides the core rendering engine that:
- Accepts RenderSpec contracts
- Dispatches to appropriate output adapters
- Handles batch rendering with parallelism
- Provides consistent styling via RenderStyle
"""

import asyncio
from datetime import datetime, timezone
from typing import TYPE_CHECKING
from uuid import uuid4

from shared.contracts.core.rendering import (
    BatchRenderRequest,
    BatchRenderResult,
    OutputFormat,
    OutputTarget,
    RenderRequest,
    RenderResult,
    RenderSpec,
    RenderState,
    RenderStyle,
    RenderedOutput,
)

if TYPE_CHECKING:
    from shared.rendering.adapters.base import BaseOutputAdapter

__version__ = "0.1.0"


class RenderEngine:
    """Unified rendering engine for all visualization tasks.

    Per ADR-0028: This is the single entry point for all rendering operations
    across DAT, SOV, and PPTX tools.

    Usage:
        engine = RenderEngine()

        # Single render
        spec = ChartSpec(chart_type=ChartType.BAR, ...)
        result = await engine.render(spec, target=OutputTarget.PNG)

        # Batch render
        results = await engine.render_batch([spec1, spec2, spec3])
    """

    def __init__(
        self,
        default_style: RenderStyle | None = None,
        default_output_path: str | None = None,
    ) -> None:
        """Initialize the rendering engine.

        Args:
            default_style: Default styling to apply to all renders.
            default_output_path: Default path prefix for output files.
        """
        self._default_style = default_style or RenderStyle()
        self._default_output_path = default_output_path or "workspace/renders"
        self._adapters: dict[OutputTarget, "BaseOutputAdapter"] = {}

    def register_adapter(
        self,
        target: OutputTarget,
        adapter: "BaseOutputAdapter",
    ) -> None:
        """Register an output adapter for a target format.

        Args:
            target: Output target (PNG, SVG, PPTX, etc.)
            adapter: Adapter implementation for this target.
        """
        self._adapters[target] = adapter

    def get_adapter(self, target: OutputTarget) -> "BaseOutputAdapter | None":
        """Get the registered adapter for a target format."""
        return self._adapters.get(target)

    async def render(
        self,
        spec: RenderSpec,
        target: OutputTarget = OutputTarget.PNG,
        output_format: OutputFormat | None = None,
        style_overrides: RenderStyle | None = None,
        output_path: str | None = None,
    ) -> RenderResult:
        """Render a single spec to the specified target.

        Args:
            spec: The render specification (ChartSpec, TableSpec, etc.)
            target: Output target format.
            output_format: Optional format configuration overrides.
            style_overrides: Optional style overrides.
            output_path: Optional output file path.

        Returns:
            RenderResult with rendered output or error details.
        """
        render_id = str(uuid4())[:8]
        started_at = datetime.now(timezone.utc).replace(microsecond=0)

        result = RenderResult(
            spec_id=spec.spec_id,
            render_id=render_id,
            state=RenderState.RENDERING,
            started_at=started_at,
        )

        try:
            # Get adapter for target
            adapter = self._adapters.get(target)
            if adapter is None:
                # Use fallback rendering if no adapter registered
                result.state = RenderState.FAILED
                result.error_message = f"No adapter registered for target: {target}"
                result.completed_at = datetime.now(timezone.utc).replace(microsecond=0)
                return result

            # Merge styles
            effective_style = self._merge_styles(
                spec.style,
                style_overrides,
            )

            # Prepare output format
            if output_format is None:
                output_format = OutputFormat(
                    target=target,
                    width_px=spec.width_px,
                    height_px=spec.height_px,
                )

            # Render via adapter
            output = await adapter.render(
                spec=spec,
                style=effective_style,
                output_format=output_format,
                output_path=output_path or self._default_output_path,
            )

            result.outputs.append(output)
            result.state = RenderState.COMPLETED
            result.completed_at = datetime.now(timezone.utc).replace(microsecond=0)

            if result.started_at and result.completed_at:
                delta = result.completed_at - result.started_at
                result.render_duration_ms = delta.total_seconds() * 1000

        except Exception as e:
            result.state = RenderState.FAILED
            result.error_message = str(e)
            result.error_details = {"exception_type": type(e).__name__}
            result.completed_at = datetime.now(timezone.utc).replace(microsecond=0)

        return result

    async def render_request(self, request: RenderRequest) -> RenderResult:
        """Render from a RenderRequest contract.

        Args:
            request: Full render request with spec and options.

        Returns:
            RenderResult with all requested outputs.
        """
        render_id = request.request_id or str(uuid4())[:8]
        started_at = datetime.now(timezone.utc).replace(microsecond=0)

        result = RenderResult(
            spec_id=request.spec.spec_id,
            render_id=render_id,
            state=RenderState.RENDERING,
            started_at=started_at,
        )

        try:
            for output_format in request.outputs:
                single_result = await self.render(
                    spec=request.spec,
                    target=output_format.target,
                    output_format=output_format,
                    style_overrides=request.style_overrides,
                    output_path=request.output_path_prefix,
                )
                result.outputs.extend(single_result.outputs)
                result.warnings.extend(single_result.warnings)

                if single_result.error_message:
                    result.warnings.append(
                        f"Output {output_format.target}: {single_result.error_message}"
                    )

            result.state = RenderState.COMPLETED
            result.completed_at = datetime.now(timezone.utc).replace(microsecond=0)

            if result.started_at and result.completed_at:
                delta = result.completed_at - result.started_at
                result.render_duration_ms = delta.total_seconds() * 1000

        except Exception as e:
            result.state = RenderState.FAILED
            result.error_message = str(e)
            result.completed_at = datetime.now(timezone.utc).replace(microsecond=0)

        return result

    async def render_batch(
        self,
        request: BatchRenderRequest,
    ) -> BatchRenderResult:
        """Render multiple specs in batch.

        Per ADR-0012: Uses asyncio for concurrent rendering.

        Args:
            request: Batch render request with multiple specs.

        Returns:
            BatchRenderResult with all results.
        """
        batch_id = str(uuid4())[:8]
        started_at = datetime.now(timezone.utc).replace(microsecond=0)

        batch_result = BatchRenderResult(
            request_id=batch_id,
            state=RenderState.RENDERING,
            total_specs=len(request.specs),
            started_at=started_at,
        )

        try:
            if request.parallel:
                # Render in parallel using asyncio
                tasks = [
                    self.render(
                        spec=spec,
                        target=request.outputs[0].target if request.outputs else OutputTarget.PNG,
                        style_overrides=request.style_overrides,
                        output_path=request.output_path_prefix,
                    )
                    for spec in request.specs
                ]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                for result in results:
                    if isinstance(result, Exception):
                        batch_result.failed_specs += 1
                        batch_result.results.append(
                            RenderResult(
                                spec_id="unknown",
                                render_id=str(uuid4())[:8],
                                state=RenderState.FAILED,
                                error_message=str(result),
                            )
                        )
                    else:
                        batch_result.results.append(result)
                        if result.state == RenderState.COMPLETED:
                            batch_result.completed_specs += 1
                        else:
                            batch_result.failed_specs += 1
            else:
                # Render sequentially
                for spec in request.specs:
                    result = await self.render(
                        spec=spec,
                        target=request.outputs[0].target if request.outputs else OutputTarget.PNG,
                        style_overrides=request.style_overrides,
                        output_path=request.output_path_prefix,
                    )
                    batch_result.results.append(result)
                    if result.state == RenderState.COMPLETED:
                        batch_result.completed_specs += 1
                    else:
                        batch_result.failed_specs += 1

            batch_result.state = RenderState.COMPLETED
            batch_result.completed_at = datetime.now(timezone.utc).replace(microsecond=0)

            if batch_result.started_at and batch_result.completed_at:
                delta = batch_result.completed_at - batch_result.started_at
                batch_result.total_duration_ms = delta.total_seconds() * 1000

        except Exception as e:
            batch_result.state = RenderState.FAILED
            batch_result.completed_at = datetime.now(timezone.utc).replace(microsecond=0)

        return batch_result

    def _merge_styles(
        self,
        spec_style: RenderStyle,
        overrides: RenderStyle | None,
    ) -> RenderStyle:
        """Merge spec style with overrides and defaults.

        Priority: overrides > spec_style > default_style
        """
        if overrides is None:
            return spec_style

        # Create merged style - override non-default values
        merged_dict = self._default_style.model_dump()
        merged_dict.update(
            {k: v for k, v in spec_style.model_dump().items() if v is not None}
        )
        merged_dict.update(
            {k: v for k, v in overrides.model_dump().items() if v is not None}
        )

        return RenderStyle.model_validate(merged_dict)
