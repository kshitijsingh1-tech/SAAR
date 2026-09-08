"""
Saar (सार) — Core Domain-Agnostic Data Models
Generic Entity, Feature, Observation, Concept, Relationship, and Evidence models.
These are NOT tied to any specific domain (agriculture, infrastructure, etc.)
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum
import uuid
from datetime import datetime


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class FeatureType(str, Enum):
    CONTINUOUS = "continuous"
    CATEGORICAL = "categorical"
    TEMPORAL = "temporal"
    BINARY = "binary"
    TEXT = "text"
    UNKNOWN = "unknown"


class SemanticRole(str, Enum):
    """What role does a column play in reasoning?"""
    TARGET = "target"              # Outcome variable (yellowing, revenue, failure)
    ENVIRONMENTAL = "environmental"  # External condition (temperature, humidity)
    INTERVENTION = "intervention"   # Action taken (watering, fertilizer, marketing spend)
    IDENTIFIER = "identifier"       # Entity ID / name
    TEMPORAL = "temporal"           # Timestamp / date
    MEASUREMENT = "measurement"     # Generic numeric measurement
    STATE = "state"                 # Current state descriptor
    UNKNOWN = "unknown"


class ConceptStatus(str, Enum):
    CANDIDATE = "candidate"
    SUPPORTED = "supported"
    WEAK = "weak"
    CONTRADICTED = "contradicted"
    UNCERTAIN = "uncertain"
    REJECTED = "rejected"


class RelationshipType(str, Enum):
    CORRELATION = "correlation"
    TEMPORAL_ASSOCIATION = "temporal_association"
    CAUSAL_HYPOTHESIS = "causal_hypothesis"
    TREND = "trend"
    BEFORE_AFTER = "before_after"
    CO_OCCURRENCE = "co_occurrence"
    DEPENDENCY = "dependency"


class EvidenceType(str, Enum):
    OBSERVATION = "observation"
    STATISTICAL = "statistical"
    USER_PROVIDED = "user_provided"
    DOMAIN_KNOWLEDGE = "domain_knowledge"
    VISUAL = "visual"
    MEASUREMENT = "measurement"


class TrendDirection(str, Enum):
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    FLUCTUATING = "fluctuating"
    INSUFFICIENT = "insufficient_data"


# ---------------------------------------------------------------------------
# Dataset & Schema Models
# ---------------------------------------------------------------------------

class ColumnProfile(BaseModel):
    """Statistical profile of a single column."""
    name: str
    dtype: str = "unknown"
    feature_type: FeatureType = FeatureType.UNKNOWN
    semantic_role: SemanticRole = SemanticRole.UNKNOWN
    non_null_count: int = 0
    null_count: int = 0
    null_pct: float = 0.0
    unique_count: int = 0
    # Numeric stats (None if categorical)
    mean: Optional[float] = None
    median: Optional[float] = None
    std: Optional[float] = None
    min_val: Optional[float] = None
    max_val: Optional[float] = None
    # Categorical stats
    top_values: Optional[List[Dict[str, Any]]] = None
    # Temporal
    date_range: Optional[Dict[str, str]] = None


class DatasetProfile(BaseModel):
    """Full profile of an uploaded dataset."""
    dataset_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    filename: str
    row_count: int
    column_count: int
    columns: List[ColumnProfile]
    temporal_columns: List[str] = Field(default_factory=list)
    numeric_columns: List[str] = Field(default_factory=list)
    categorical_columns: List[str] = Field(default_factory=list)
    missing_summary: Dict[str, float] = Field(default_factory=dict)
    initial_observations: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


# ---------------------------------------------------------------------------
# Entity / Feature / Observation Models
# ---------------------------------------------------------------------------

class Entity(BaseModel):
    """Something SAAR reasons about (Plant, Machine, Customer, etc.)."""
    entity_id: str = Field(default_factory=lambda: f"ENT-{str(uuid.uuid4())[:6]}")
    entity_type: str = "generic"
    name: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Feature(BaseModel):
    """A measurable attribute of an entity."""
    feature_id: str = Field(default_factory=lambda: f"FEAT-{str(uuid.uuid4())[:6]}")
    entity_id: Optional[str] = None
    name: str
    feature_type: FeatureType = FeatureType.CONTINUOUS
    semantic_role: SemanticRole = SemanticRole.MEASUREMENT
    unit: Optional[str] = None
    description: Optional[str] = None


class Observation(BaseModel):
    """A single data point: who/what + when + value + source."""
    observation_id: str = Field(default_factory=lambda: f"OBS-{str(uuid.uuid4())[:6]}")
    entity_id: Optional[str] = None
    feature_name: str
    value: Any
    unit: Optional[str] = None
    timestamp: Optional[str] = None
    source: str = "dataset"
    confidence: float = 1.0


# ---------------------------------------------------------------------------
# Concept / Hypothesis Models
# ---------------------------------------------------------------------------

class Concept(BaseModel):
    """A candidate explanation that needs evidence."""
    concept_id: str = Field(default_factory=lambda: f"C-{str(uuid.uuid4())[:6]}")
    name: str
    concept_type: str = "hypothesis"
    category: str = "hypothesis"
    status: ConceptStatus = ConceptStatus.CANDIDATE
    supporting_relationships: List[str] = Field(default_factory=list)
    supporting_evidence: List[str] = Field(default_factory=list)
    contradicting_evidence: List[str] = Field(default_factory=list)
    confidence: float = 0.5
    unknowns: List[str] = Field(default_factory=list)
    description: Optional[str] = None


# ---------------------------------------------------------------------------
# Relationship & Evidence Models
# ---------------------------------------------------------------------------

class Evidence(BaseModel):
    """Traceable evidence supporting or contradicting a relationship."""
    evidence_id: str = Field(default_factory=lambda: f"E-{str(uuid.uuid4())[:6]}")
    evidence_type: EvidenceType = EvidenceType.OBSERVATION
    description: str = ""
    observation: Optional[str] = None
    observation_ids: List[str] = Field(default_factory=list)
    source: str = "dataset"
    value: Optional[Any] = None
    confidence: float = 1.0
    timestamp: Optional[str] = None
    impact: Optional[str] = None
    weight: Optional[float] = None


class Relationship(BaseModel):
    """A discovered relationship between two features/concepts."""
    relationship_id: str = Field(default_factory=lambda: f"REL-{str(uuid.uuid4())[:6]}")
    source_feature: str
    target_feature: str
    relationship_type: RelationshipType = RelationshipType.CORRELATION
    direction: Optional[str] = None        # "positive", "negative", "none"
    strength: Optional[float] = None       # correlation coefficient
    confidence: float = 0.5
    observation_count: int = 0
    time_window: Optional[str] = None
    supporting_evidence: List[str] = Field(default_factory=list)
    contradicting_evidence: List[str] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)
    causal_claim: bool = False             # NEVER True without explicit justification
    description: Optional[str] = None


class TrendResult(BaseModel):
    """Trend detection result for a feature."""
    feature_name: str
    direction: TrendDirection
    slope: Optional[float] = None
    r_squared: Optional[float] = None
    observation_count: int = 0
    time_window: Optional[str] = None
    description: Optional[str] = None


# ---------------------------------------------------------------------------
# Question & Answer Models
# ---------------------------------------------------------------------------

class GeneratedQuestion(BaseModel):
    """A question SAAR generates to reduce uncertainty."""
    question_id: str = Field(default_factory=lambda: f"Q-{str(uuid.uuid4())[:6]}")
    question: str
    targets_uncertainty: List[str] = Field(default_factory=list)
    expected_information_gain: float = 0.5
    priority: str = "medium"  # high, medium, low
    reason: Optional[str] = None


class UserAnswer(BaseModel):
    """A user's answer that becomes structured evidence."""
    question_id: Optional[str] = None
    raw_answer: str
    structured_data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


# ---------------------------------------------------------------------------
# Investigation State Model
# ---------------------------------------------------------------------------

class InvestigationState(BaseModel):
    """The full state of an active SAAR investigation."""
    investigation_id: str = Field(default_factory=lambda: f"INV-{str(uuid.uuid4())[:8]}")
    dataset_id: Optional[str] = None
    dataset_profile: Optional[DatasetProfile] = None
    entities: List[Entity] = Field(default_factory=list)
    features: List[Feature] = Field(default_factory=list)
    observations: List[Observation] = Field(default_factory=list)
    concepts: List[Concept] = Field(default_factory=list)
    relationships: List[Relationship] = Field(default_factory=list)
    evidence: List[Evidence] = Field(default_factory=list)
    trends: List[TrendResult] = Field(default_factory=list)
    questions: List[GeneratedQuestion] = Field(default_factory=list)
    answers: List[UserAnswer] = Field(default_factory=list)
    iteration: int = 0
    overall_confidence: float = 0.0
    status: str = "active"  # active, concluded, insufficient_data
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
