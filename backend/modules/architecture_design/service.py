"""

ArchitectureDesignService – Architecture Decision Agent entry point.

Milestone 1:  run(batch)               → ClassificationOutput

Milestone 2:  evaluate(batch)          → ScoringOutput

Milestone 3:  retrieve_evidence(batch) → RetrievalOutput

Milestone 4:  recommend(batch)         → RecommendationOutput

Milestone 5:  generate_design(batch)   → ArchitectureDesignOutput

The classifier is injectable (default: KeywordClassifier).

The scorer loads the knowledge base once at import time.

The retriever embeds knowledge items once at construction time.

The LLM Provider handles structured generations and is injectable.

"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

from .knowledge.architecture_scorer import score as _score_profile

from .quality_classifier import BaseClassifier, KeywordClassifier

from .quality_profile import build_profile

from .retrieval.embedding_provider import BaseEmbeddingProvider

from .retrieval.retriever import ArchitectureRetriever, build_query

from .retrieval.vector_store import BaseVectorStore

from .llm.provider import BaseLLMProvider, GeminiLLMProvider, StubLLMProvider

from .llm.prompts import build_recommendation_prompt

from .llm.design_prompts import build_design_prompt

from .plantuml_generator import generate_plantuml

from .schemas import (

    ASRBatch,

    ArchitectureProjectInput,

    ASRClassification,

    ClassificationOutput,

    QualityAttribute,

    RetrievalOutput,

    ScoringOutput,

    ArchitectureRecommendation,

    RecommendationOutput,

    HighLevelArchitectureDesign,

    ArchitectureDesignOutput,

    ExecutionMetadata,

    ArchitectureAnalysisOutput,

)

class ArchitectureDesignService:

    """

    Public façade for the Architecture Decision Agent.

    Usage – Milestone 1:

        svc = ArchitectureDesignService()

        output: ClassificationOutput = svc.run(batch)

    Usage – Milestone 2:

        svc = ArchitectureDesignService()

        output: ScoringOutput = svc.evaluate(batch)

    Usage – Milestone 4:

        svc = ArchitectureDesignService()

        output: RecommendationOutput = svc.recommend(batch)

    Usage – Milestone 5:

        svc = ArchitectureDesignService()

        output: ArchitectureDesignOutput = svc.generate_design(batch)

    Args:

        classifier:          Optional custom classifier. Defaults to KeywordClassifier.

        embedding_provider:  Optional embedding provider. Defaults to

                             SentenceTransformerEmbeddingProvider (all-MiniLM-L6-v2).

        vector_store:        Optional vector store. Defaults to InMemoryVectorStore.

        llm_provider:        Optional LLM provider. Defaults to GeminiLLMProvider.

    """

    def __init__(

        self,

        classifier:         BaseClassifier         | None = None,

        embedding_provider: BaseEmbeddingProvider  | None = None,

        vector_store:       BaseVectorStore        | None = None,

        llm_provider:       BaseLLMProvider        | None = None,

    ) -> None:

        self._classifier: BaseClassifier = classifier or KeywordClassifier()

        # Retriever and LLM are lazy-initialised to save memory/startup time

        self._embedding_provider = embedding_provider

        self._vector_store       = vector_store

        self._retriever: ArchitectureRetriever | None = None

        self._llm_provider: BaseLLMProvider | None = llm_provider


    def _artifact_directory(self) -> Path:
        """
        Return the Architecture Decision artifact directory, creating it when
        necessary.

        Outputs are kept separate from other DesignTrace AI modules:
            backend/outputs/architecture_designs/artifacts/
        """
        backend_dir = Path(__file__).resolve().parents[2]
        artifact_dir = (
            backend_dir
            / "outputs"
            / "architecture_designs"
            / "artifacts"
        )
        artifact_dir.mkdir(parents=True, exist_ok=True)
        return artifact_dir

    @staticmethod
    def _safe_artifact_stem(project_id: str) -> str:
        """Convert a project ID into a safe cross-platform filename stem."""
        cleaned = re.sub(
            r"[^A-Za-z0-9._-]+",
            "_",
            project_id.strip(),
        )
        cleaned = cleaned.strip("._-")
        return cleaned or "architecture_project"

    def _save_analysis_artifacts(
        self,
        analysis: ArchitectureAnalysisOutput,
    ) -> dict[str, str]:
        """
        Persist the latest successful architecture-analysis artifacts.

        The full analysis JSON is the canonical persisted result. Separate
        recommendation/design JSON and PlantUML files are also written for
        easier inspection by the team and supervisors.

        Stub-based test runs are intentionally not persisted so the test suite
        does not create repository artifacts.
        """
        if isinstance(
            self._llm_provider,
            StubLLMProvider,
        ):
            return {}

        artifact_dir = self._artifact_directory()
        stem = self._safe_artifact_stem(
            analysis.project_id
        )

        analysis_path = (
            artifact_dir
            / f"{stem}_analysis.json"
        )

        recommendation_path = (
            artifact_dir
            / f"{stem}_recommendation.json"
        )

        design_path = (
            artifact_dir
            / f"{stem}_design.json"
        )

        plantuml_path = (
            artifact_dir
            / f"{stem}_architecture.puml"
        )

        analysis_path.write_text(
            json.dumps(
                analysis.model_dump(
                    mode="json"
                ),
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        recommendation_path.write_text(
            json.dumps(
                analysis.result.recommendation.model_dump(
                    mode="json"
                ),
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        design_path.write_text(
            json.dumps(
                analysis.result.design.model_dump(
                    mode="json"
                ),
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        plantuml_path.write_text(
            analysis.result.plantuml,
            encoding="utf-8",
        )

        return {
            "analysis": str(
                analysis_path
            ),
            "recommendation": str(
                recommendation_path
            ),
            "design": str(
                design_path
            ),
            "plantuml": str(
                plantuml_path
            ),
        }

    def _normalise_project_input(

        self,

        project: ArchitectureProjectInput | ASRBatch,

    ) -> ArchitectureProjectInput:

        """

        Convert legacy ASRBatch input into the new full project input shape.

        This keeps older service-level tests and internal callers compatible

        while the public M5 /analyze API uses ArchitectureProjectInput.

        When only an ASRBatch is available, the ASRs are promoted to the

        requirements collection with requirement_type='other'. This fallback

        cannot create a complete domain architecture, but it preserves the

        previous ASR-only behaviour for legacy callers and tests.

        """

        if isinstance(project, ArchitectureProjectInput):

            return project

        if isinstance(project, ASRBatch):

            return ArchitectureProjectInput(

                project_id=project.project_id,

                requirements=[

                    {

                        "requirement_id": asr.requirement_id,

                        "statement": asr.statement,

                        "requirement_type": "other",

                    }

                    for asr in project.asrs

                ],

                asrs=project.asrs,

            )

        raise TypeError(

            "Expected ArchitectureProjectInput or ASRBatch."

        )

    # ------------------------------------------------------------------

    # Milestone 1 – Classification pipeline

    # ------------------------------------------------------------------

    def run(self, batch: ASRBatch) -> ClassificationOutput:

        """

        ASRBatch → ClassificationOutput  (Milestone 1 pipeline, unchanged).

        Steps:

            1. Classify each ASR statement into quality attributes.

            2. Build the project-level quality profile.

            3. Return a fully Pydantic-validated ClassificationOutput.

        """

        classifications: list[ASRClassification] = []

        for asr in batch.asrs:

            hits = self._classifier.classify(asr.statement)

            classifications.append(

                ASRClassification(

                    requirement_id=asr.requirement_id,

                    quality_attributes=hits,

                )

            )

        profile = build_profile(classifications)

        return ClassificationOutput(

            project_id=batch.project_id,

            classifications=classifications,

            quality_profile=profile,

        )

    # ------------------------------------------------------------------

    # Milestone 2 – Scoring pipeline

    # ------------------------------------------------------------------

    def evaluate(self, batch: ASRBatch) -> ScoringOutput:

        """

        ASRBatch → ScoringOutput  (Milestone 2 pipeline).

        Steps:

            1. Run the Milestone 1 classification pipeline to get the profile.

            2. Derive quality weights from the profile.

            3. Score all architecture styles against those weights.

            4. Return a Pydantic-validated ScoringOutput with ranked evaluations.

        """

        classification_output = self.run(batch)

        profile = classification_output.quality_profile

        evaluations = _score_profile(profile)

        return ScoringOutput(

            project_id=batch.project_id,

            quality_profile=profile,

            architecture_evaluations=evaluations,

        )

    # ------------------------------------------------------------------

    # Milestone 3 – RAG evidence retrieval

    # ------------------------------------------------------------------

    def retrieve_evidence(

        self,

        batch: ASRBatch,

        top_k: int = 5,

    ) -> RetrievalOutput:

        """

        ASRBatch → RetrievalOutput  (Milestone 3 pipeline).

        Steps:

            1. Run M1 classification to get QualityProfile.

            2. Run M2 scoring to identify top-ranked architecture styles.

            3. Build a retrieval query from active QAs + top styles + ASR text.

            4. Retrieve the most relevant knowledge items.

            5. Return a Pydantic-validated RetrievalOutput.

        Args:

            batch:  Validated ASRBatch.

            top_k:  Maximum number of evidence items to return.

        Returns:

            RetrievalOutput with ordered evidence list.

        """

        # Lazy-init the retriever (loads embedding model on first call)

        if self._retriever is None:

            self._retriever = ArchitectureRetriever(

                embedding_provider = self._embedding_provider,

                vector_store       = self._vector_store,

            )

        classification_output = self.run(batch)

        profile   = classification_output.quality_profile

        scoring   = self.evaluate(batch)

        # Active quality attributes ordered by count descending

        profile_counts = profile.model_dump()           # {attr: count}

        active_qas = [

            attr

            for attr in sorted(

                profile_counts,

                key=lambda a: profile_counts[a],

                reverse=True,

            )

            if profile_counts[attr] > 0

        ]

        # Top-N architecture styles from M2 ranking

        top_styles = [

            ev.style.value

            for ev in scoring.architecture_evaluations

            if ev.rank <= 3              # top-3 candidates in query

        ]

        # ASR statements (raw text)

        asr_texts = [asr.statement for asr in batch.asrs]

        query    = build_query(active_qas, top_styles, asr_texts)

        evidence = self._retriever.retrieve(query, top_k=top_k)

        return RetrievalOutput(

            project_id        = batch.project_id,

            query             = query,

            top_architectures = top_styles,

            evidence          = evidence,

        )

    # ------------------------------------------------------------------

    # Milestone 4 – LLM Explainable Architecture Recommendation

    # ------------------------------------------------------------------

    def recommend(

        self,

        batch: ASRBatch,

        top_k: int = 5,

    ) -> RecommendationOutput:

        """

        ASRBatch → RecommendationOutput (Milestone 4 pipeline).

        Steps:

            1. Run M1, M2, and M3 pipelines.

            2. Build structured LLM prompt mapping all deterministic data.

            3. Generate ArchitectureRecommendation using the LLM.

            4. Enforce strict deterministic guardrails on LLM output to prevent hallucination.

            5. Return validated RecommendationOutput.

        """

        # 1. Run all prior pipelines

        scoring_out   = self.evaluate(batch)

        retrieval_out = self.retrieve_evidence(batch, top_k=top_k)

        # 2. Build Prompt

        prompt = build_recommendation_prompt(

            batch       = batch,

            profile     = scoring_out.quality_profile,

            evaluations = scoring_out.architecture_evaluations,

            evidence    = retrieval_out.evidence,

        )

        # 3. Call LLM

        if self._llm_provider is None:

            self._llm_provider = GeminiLLMProvider()

        raw_rec = self._llm_provider.generate_structured(prompt, ArchitectureRecommendation)

        # 4. Strict Deterministic Guardrails

        # Sort evaluations by rank to find the true Rank 1

        sorted_evals = sorted(scoring_out.architecture_evaluations, key=lambda e: e.rank)

        rank_1_evals = [e for e in sorted_evals if e.rank == 1]

        rank_1_styles = {e.style.value: e.normalized_score for e in rank_1_evals}

        selected_style = raw_rec.selected_style

        score          = raw_rec.score

        tied_candidates = [e.style.value for e in rank_1_evals] if len(rank_1_evals) > 1 else []

        tie_resolved = raw_rec.tie_resolved

        tie_resolution_reason = raw_rec.tie_resolution_reason

        review_required = raw_rec.review_required

        # Guardrail 1: Enforce Rank 1 Selection & Score

        if selected_style not in rank_1_styles:

            # The LLM hallucinated entirely or chose a lower rank.

            # Force patch to the first deterministic Rank 1 candidate.

            selected_style = rank_1_evals[0].style.value

            score = rank_1_evals[0].normalized_score

            review_required = True

            tie_resolved = False

        else:

            # The selection is a valid Rank 1 candidate. Enforce exact deterministic score.

            score = rank_1_styles[selected_style]

        # Guardrail 2: Validate tie-resolution integrity

        if len(rank_1_evals) > 1:

            if not tie_resolution_reason or not tie_resolved:

                # The LLM failed to resolve the tie meaningfully, force a review.

                review_required = True

                tie_resolved = False

        # Guardrail 3: Ensure rejected alternatives actually exist in M2 list

        valid_styles = {e.style.value: e.normalized_score for e in sorted_evals}

        safe_rejected = []

        for alt in raw_rec.rejected_alternatives:

            if alt.style in valid_styles and alt.style != selected_style:

                # Patch score if hallucinated

                alt.score = valid_styles[alt.style]

                safe_rejected.append(alt)

        # Guardrail 4: Strip hallucinated evidence IDs

        valid_ids = {ev.knowledge_id for ev in retrieval_out.evidence}

        safe_evidence_ids = [eid for eid in raw_rec.evidence_ids if eid in valid_ids]

        # 5. Reconstruct final safe model

        safe_rec = ArchitectureRecommendation(

            selected_style         = selected_style,

            score                  = score,

            rationale              = raw_rec.rationale,

            key_quality_attributes = raw_rec.key_quality_attributes,

            strengths              = raw_rec.strengths,

            weaknesses             = raw_rec.weaknesses,

            tradeoffs              = raw_rec.tradeoffs,

            rejected_alternatives  = safe_rejected,

            evidence_ids           = safe_evidence_ids,

            tied_candidates        = tied_candidates,

            tie_resolved           = tie_resolved,

            tie_resolution_reason  = tie_resolution_reason,

            review_required        = review_required,

        )

        return RecommendationOutput(

            project_id=batch.project_id,

            recommendation=safe_rec,

        )

    # ------------------------------------------------------------------

    # Milestone 5 – High-Level Architecture Design Generation

    # ------------------------------------------------------------------

    def generate_design(

        self,

        project: ArchitectureProjectInput | ASRBatch,

        top_k: int = 5,

    ) -> ArchitectureDesignOutput:

        """

        Generate the complete high-level architecture. ASRs drive M1-M4

        architecture decision-making, while all project requirements drive

        requirement-derived component generation and traceability.

        """

        project = self._normalise_project_input(project)

        batch = project.to_asr_batch()

        rec_out = self.recommend(batch, top_k=top_k)

        scoring_out = self.evaluate(batch)

        retrieval_out = self.retrieve_evidence(batch, top_k=top_k)

        prompt = build_design_prompt(

            project=project,

            profile=scoring_out.quality_profile,

            recommendation=rec_out.recommendation,

            evidence=retrieval_out.evidence,

        )

        if self._llm_provider is None:

            self._llm_provider = GeminiLLMProvider()

        raw_design = self._llm_provider.generate_structured(

            prompt,

            HighLevelArchitectureDesign,

        )

        valid_req_ids = {r.requirement_id for r in project.requirements}

        valid_comp_ids = set()

        valid_qa_values = {qa.value for qa in QualityAttribute}

        safe_components = []

        for comp in raw_design.components:

            if comp.component_id in valid_comp_ids:

                comp.component_id = f"{comp.component_id}_dup"

            comp.related_requirements = [

                req for req in comp.related_requirements if req in valid_req_ids

            ]

            if comp.grounding_type == "requirement_derived" and not comp.related_requirements:

                continue

            comp.related_quality_attributes = [

                qa for qa in comp.related_quality_attributes

                if getattr(qa, "value", qa) in valid_qa_values

            ]

            valid_comp_ids.add(comp.component_id)

            safe_components.append(comp)

        safe_connections = [

            conn for conn in raw_design.connections

            if conn.source in valid_comp_ids and conn.target in valid_comp_ids

        ]

        safe_style = rec_out.recommendation.selected_style

        valid_ev_ids = {ev.knowledge_id for ev in retrieval_out.evidence}

        safe_ev_ids = [eid for eid in raw_design.evidence_ids if eid in valid_ev_ids]

        safe_design = HighLevelArchitectureDesign(

            style=safe_style,

            components=safe_components,

            connections=safe_connections,

            design_rationale=raw_design.design_rationale,

            evidence_ids=safe_ev_ids,

        )

        plantuml_str = generate_plantuml(safe_design)

        return ArchitectureDesignOutput(

            project_id=project.project_id,

            recommendation=rec_out.recommendation,

            design=safe_design,

            plantuml=plantuml_str,

        )

    # ------------------------------------------------------------------

    # Milestone 7.3 – Full Pipeline Analysis with Full-Requirement Design Context

    # ------------------------------------------------------------------

    def analyze(

        self,

        project: ArchitectureProjectInput | ASRBatch,

        top_k: int = 5,

    ) -> ArchitectureAnalysisOutput:

        """Run ASR-based architecture decision plus full-requirement design generation."""

        start_time = time.perf_counter()

        project = self._normalise_project_input(project)

        batch = project.to_asr_batch()

        classification_output = self.run(batch)

        scoring_output = self.evaluate(batch)

        retrieval_output = self.retrieve_evidence(batch, top_k=top_k)

        design_output = self.generate_design(project, top_k=top_k)

        duration_ms = (time.perf_counter() - start_time) * 1000.0

        classifier_name = type(self._classifier).__name__

        if self._embedding_provider is not None:

            embedding_model = getattr(

                self._embedding_provider, "model_name", type(self._embedding_provider).__name__

            )

        else:

            embedding_model = "sentence-transformers/all-MiniLM-L6-v2"

        if self._llm_provider is not None:

            llm_provider = type(self._llm_provider).__name__

            llm_model = getattr(

                self._llm_provider,

                "model_name",

                "stub" if isinstance(self._llm_provider, StubLLMProvider) else "gemini-3.5-flash-lite",

            )

        else:

            llm_provider = "GeminiLLMProvider"

            llm_model = "gemini-3.5-flash-lite"

        metadata = ExecutionMetadata(

            pipeline_version="M7.3",

            classifier_name=classifier_name,

            embedding_model=embedding_model,

            llm_provider=llm_provider,

            llm_model=llm_model,

            retrieval_top_k=top_k,

            execution_time_ms=round(duration_ms, 2),

        )

        analysis_output = ArchitectureAnalysisOutput(
            project_id=project.project_id,
            classification=classification_output,
            scoring=scoring_output,
            retrieval=retrieval_output,
            result=design_output,
            metadata=metadata,
        )

        self._save_analysis_artifacts(
            analysis_output
        )

        return analysis_output

