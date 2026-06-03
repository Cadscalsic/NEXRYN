import {
  Activity,
  Archive,
  Atom,
  BrainCircuit,
  Gauge,
  CircleGauge,
  ClipboardCheck,
  Cross,
  Dna,
  FileClock,
  FlaskConical,
  GitBranch,
  HeartPulse,
  MemoryStick,
  LayoutDashboard,
  Network,
  ShieldCheck,
  Sparkles,
  Stethoscope,
  TriangleAlert,
  Waves,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

export type PageId =
  | "overview"
  | "cognitive-health"
  | "pharmacy"
  | "dna"
  | "graveyard"
  | "governance";
export type Tone = "cyan" | "mint" | "violet" | "amber";
export type ProtocolStatus = "Available" | "Recommended" | "Locked" | "Standby";
export type RiskLevel = "Low" | "Medium" | "High";
export type TraitStatus = "Core" | "Adaptive" | "Watched";

export type NavItem = {
  label: string;
  pageId?: PageId;
  enabled: boolean;
  icon: LucideIcon;
};

export type RuntimeStatus = {
  label: string;
  value: string;
  tone: Tone;
};

export type StatusCardData = {
  label: string;
  value: string;
  detail: string;
  metric: number;
  tone: Tone;
  icon: LucideIcon;
};

export type VitalMetric = {
  label: string;
  value: string;
  meter: number;
};

export type SemanticNode = {
  label: string;
  x: number;
  y: number;
  tone: "cyan" | "mint" | "violet" | "amber" | "blue";
};

export type HealthMetric = {
  label: string;
  value: string;
  detail: string;
  meter: number;
  tone: Tone;
  icon: LucideIcon;
};

export type DiagnosisCategory = {
  label: string;
  active: boolean;
  tone: Tone;
};

export type PhysicianDiagnosis = {
  diagnosis: string;
  severity: string;
  recommendation: string;
  treatmentRequired: boolean;
  monitoringRequired: boolean;
  riskLevel: string;
};

export type PharmacyProtocol = {
  id: string;
  name: string;
  category: string;
  purpose: string;
  status: ProtocolStatus;
  intensity: RiskLevel;
  dependencyRisk: RiskLevel;
  sideEffectRisk: RiskLevel;
  constitutionalApprovalRequired: boolean;
  tone: Tone;
  icon: LucideIcon;
};

export type PhysicianProtocolRecommendation = {
  currentDiagnosis: string;
  recommendedProtocol: string;
  suggestedAction: string;
};

export type CognitiveDNAHealth = {
  dnaStability: number;
  traitIntegrity: number;
  mutationPressure: number;
  invariantProtection: number;
  cooperationBias: number;
  curiosityBalance: number;
  antiDominationStrength: number;
};

export type DNATrait = {
  id: string;
  name: string;
  constitutionalRole: string;
  description: string;
  whyItMatters: string;
  protectedBehaviors: string[];
  failureRisks: string[];
  connectedSystems: string[];
  suggestedMonitoring: string;
  stabilityScore: number;
  inheritanceStrength: number;
  mutationResistance: number;
  adaptiveWeight: number;
  status: TraitStatus;
  riskIfWeakened: string;
  tone: Tone;
};

export type GraveyardHealth = {
  graveyardPressure: number;
  extinctTraits: number;
  rejectedMerges: number;
  failedLineages: number;
  entropyPrunedStrategies: number;
  ontologyDamage: number;
  recoveryActions: number;
  memoryScarCount: number;
};

export type GraveyardItem = {
  id: string;
  name: string;
  type: string;
  reason: string;
  netFitness: number;
  stabilityScore: number;
  lastSeen: string;
  recoveryPotential: RiskLevel;
  status: string;
};

export type GraveyardPressureFactors = {
  failedMergePressure: number;
  extinctTraitPressure: number;
  ontologyDamagePressure: number;
  entropyPruningPressure: number;
  unstableLineagePressure: number;
  recoveryDebt: number;
};

export type GovernanceKernel = {
  kernelState: string;
  constitutionalIntegrity: number;
  policyEnforcement: number;
  mutationApprovalState: string;
  truthValidationState: string;
  runtimeAuthority: string;
  protectedInvariants: number;
  safetyGateStatus: string;
};

export type KernelPolicy = {
  id: string;
  name: string;
  status: string;
  priority: RiskLevel;
  enforcementLevel: RiskLevel;
  affectedSystems: string[];
  violationRisk: RiskLevel;
};

export type ProtectedInvariant = {
  id: string;
  name: string;
  strength: number;
  status: string;
  protectedReason: string;
};

export type ApprovalRequest = {
  id: string;
  request: string;
  sourceSystem: string;
  riskLevel: RiskLevel;
  status: string;
  requiredApproval: string;
  reason: string;
};

export const navItems: NavItem[] = [
  { label: "Overview", pageId: "overview", enabled: true, icon: LayoutDashboard },
  { label: "Cognitive Health", pageId: "cognitive-health", enabled: true, icon: HeartPulse },
  { label: "Governance Kernel", pageId: "governance", enabled: true, icon: ShieldCheck },
  { label: "Semantic Graph", enabled: false, icon: Network },
  { label: "DNA System", pageId: "dna", enabled: true, icon: Dna },
  { label: "Physician", enabled: false, icon: Cross },
  { label: "Pharmacy", pageId: "pharmacy", enabled: true, icon: FlaskConical },
  { label: "Graveyard", pageId: "graveyard", enabled: true, icon: Archive },
  { label: "Logs", enabled: false, icon: FileClock },
];

export const runtimeStatus: RuntimeStatus[] = [
  { label: "Runtime Status", value: "Active", tone: "mint" },
  { label: "Mode", value: "Stabilization", tone: "cyan" },
  { label: "Energy Management", value: "Active", tone: "violet" },
  { label: "Recovery Protocol", value: "Standby", tone: "amber" },
];

export const statusCards: StatusCardData[] = [
  {
    label: "Cognitive Mode",
    value: "Stabilization",
    detail: "Constitutional boundaries engaged",
    metric: 0.82,
    tone: "cyan",
    icon: BrainCircuit,
  },
  {
    label: "Entropy Risk",
    value: "0.60",
    detail: "Monitored under active damping",
    metric: 0.6,
    tone: "amber",
    icon: TriangleAlert,
  },
  {
    label: "Identity Stability",
    value: "0.84",
    detail: "Core anchors remain coherent",
    metric: 0.84,
    tone: "mint",
    icon: ShieldCheck,
  },
  {
    label: "Semantic Spine",
    value: "Guarded",
    detail: "Spine preservation layer online",
    metric: 0.78,
    tone: "violet",
    icon: GitBranch,
  },
  {
    label: "Mutation Activity",
    value: "Low",
    detail: "Unsafe changes held for review",
    metric: 0.15,
    tone: "cyan",
    icon: Atom,
  },
  {
    label: "Exploration State",
    value: "Bounded",
    detail: "Novelty allowed inside limits",
    metric: 0.38,
    tone: "mint",
    icon: Sparkles,
  },
  {
    label: "Governance Kernel",
    value: "Online",
    detail: "Judicial runtime synchronized",
    metric: 0.91,
    tone: "violet",
    icon: CircleGauge,
  },
  {
    label: "Recovery Protocol",
    value: "Standby",
    detail: "Recovery loops prepared",
    metric: 0.26,
    tone: "amber",
    icon: Activity,
  },
];

export const cognitiveVitals: VitalMetric[] = [
  { label: "Entropy Risk", value: "0.60", meter: 0.6 },
  { label: "Cognitive Pressure", value: "0.16", meter: 0.16 },
  { label: "Reasoning Depth", value: "4", meter: 0.5 },
  { label: "Mutation Rate", value: "0.15", meter: 0.15 },
  { label: "Exploration Rate", value: "0.15", meter: 0.15 },
  { label: "Semantic Specificity", value: "1.00", meter: 1 },
];

export const semanticNodes: SemanticNode[] = [
  { label: "Identity", x: 50, y: 22, tone: "cyan" },
  { label: "Memory", x: 27, y: 43, tone: "violet" },
  { label: "Causality", x: 70, y: 44, tone: "mint" },
  { label: "Semantic Consistency", x: 50, y: 58, tone: "blue" },
  { label: "Reputation", x: 32, y: 76, tone: "amber" },
  { label: "Survival History", x: 69, y: 76, tone: "cyan" },
];

export const cognitiveHealthRuntime = {
  cognitiveFeverScore: 0.28,
  identityStability: 0.84,
  entropyRisk: 0.6,
  semanticDrift: 0.22,
  memoryPressure: 0.34,
  mutationPressure: 0.15,
  graveyardPressure: 0.19,
  recoveryState: "Standby",
  cognitivePressure: 0.16,
  recoveryRecommendation: "Continue stabilization mode",
};

export function resolvePhysicianDiagnosis(): PhysicianDiagnosis {
  const entropyRisk = cognitiveHealthRuntime.entropyRisk;
  const identityStability = cognitiveHealthRuntime.identityStability;
  const mutationPressure = cognitiveHealthRuntime.mutationPressure;

  if (mutationPressure > 0.55) {
    return {
      diagnosis: "Evolutionary Pressure",
      severity: "Medium",
      recommendation: "Reduce mutation activity and preserve identity anchors",
      treatmentRequired: false,
      monitoringRequired: true,
      riskLevel: "Controlled",
    };
  }

  if (entropyRisk > 0.65) {
    return {
      diagnosis: "Monitored Instability",
      severity: "Medium",
      recommendation: "Continue stabilization mode with tighter entropy damping",
      treatmentRequired: false,
      monitoringRequired: true,
      riskLevel: "Controlled",
    };
  }

  if (entropyRisk <= 0.6 && identityStability >= 0.78) {
    return {
      diagnosis: "Stable but monitored",
      severity: "Low to Medium",
      recommendation: "Continue stabilization mode",
      treatmentRequired: false,
      monitoringRequired: true,
      riskLevel: "Controlled",
    };
  }

  return {
    diagnosis: "Temporary Overload",
    severity: "Medium",
    recommendation: "Preserve recovery posture and reduce cognitive pressure",
    treatmentRequired: false,
    monitoringRequired: true,
    riskLevel: "Controlled",
  };
}

export const physicianDiagnosis = resolvePhysicianDiagnosis();

const diagnosisCategorySeeds: Array<Omit<DiagnosisCategory, "active">> = [
  { label: "Healthy Exploration", tone: "mint" },
  { label: "Temporary Overload", tone: "amber" },
  { label: "Semantic Inflammation", tone: "violet" },
  { label: "Identity Fracture Risk", tone: "amber" },
  { label: "Recursive Exhaustion", tone: "cyan" },
  { label: "Evolutionary Pressure", tone: "violet" },
  { label: "Graveyard Pressure", tone: "amber" },
];

export const diagnosisCategories: DiagnosisCategory[] = diagnosisCategorySeeds.map((category) => ({
  ...category,
  active: category.label === physicianDiagnosis.diagnosis,
}));

export const preparedDiagnosisCategories: DiagnosisCategory[] = [
  { label: "Healthy Exploration", active: false, tone: "mint" },
  { label: "Temporary Overload", active: false, tone: "amber" },
  { label: "Semantic Inflammation", active: false, tone: "violet" },
  { label: "Identity Fracture Risk", active: false, tone: "amber" },
  { label: "Recursive Exhaustion", active: false, tone: "cyan" },
  { label: "Evolutionary Pressure", active: false, tone: "violet" },
  { label: "Graveyard Pressure", active: false, tone: "amber" },
];

export const cognitiveHealthMetrics: HealthMetric[] = [
  {
    label: "Cognitive Fever Score",
    value: cognitiveHealthRuntime.cognitiveFeverScore.toFixed(2),
    detail: "Thermal load across active reasoning layers",
    meter: cognitiveHealthRuntime.cognitiveFeverScore,
    tone: "cyan",
    icon: Stethoscope,
  },
  {
    label: "Identity Stability",
    value: cognitiveHealthRuntime.identityStability.toFixed(2),
    detail: "Continuity of identity anchors",
    meter: cognitiveHealthRuntime.identityStability,
    tone: "mint",
    icon: ShieldCheck,
  },
  {
    label: "Entropy Risk",
    value: cognitiveHealthRuntime.entropyRisk.toFixed(2),
    detail: "Disorder pressure under observation",
    meter: cognitiveHealthRuntime.entropyRisk,
    tone: "amber",
    icon: TriangleAlert,
  },
  {
    label: "Semantic Drift",
    value: cognitiveHealthRuntime.semanticDrift.toFixed(2),
    detail: "Meaning deviation from constitutional anchors",
    meter: cognitiveHealthRuntime.semanticDrift,
    tone: "violet",
    icon: Waves,
  },
  {
    label: "Memory Pressure",
    value: cognitiveHealthRuntime.memoryPressure.toFixed(2),
    detail: "Compression and retention load",
    meter: cognitiveHealthRuntime.memoryPressure,
    tone: "cyan",
    icon: MemoryStick,
  },
  {
    label: "Mutation Pressure",
    value: cognitiveHealthRuntime.mutationPressure.toFixed(2),
    detail: "Evolutionary modification pressure",
    meter: cognitiveHealthRuntime.mutationPressure,
    tone: "violet",
    icon: Atom,
  },
  {
    label: "Recovery State",
    value: cognitiveHealthRuntime.recoveryState,
    detail: "Recovery loops prepared but inactive",
    meter: 0.26,
    tone: "mint",
    icon: Activity,
  },
  {
    label: "Cognitive Pressure",
    value: cognitiveHealthRuntime.cognitivePressure.toFixed(2),
    detail: "Active load on reasoning and governance",
    meter: cognitiveHealthRuntime.cognitivePressure,
    tone: "cyan",
    icon: Gauge,
  },
];

export const protocolSimulationMode = true;

export function resolvePhysicianRecommendedProtocol(): PhysicianProtocolRecommendation {
  if (cognitiveHealthRuntime.graveyardPressure > 0.65) {
    return {
      currentDiagnosis: physicianDiagnosis.diagnosis,
      recommendedProtocol: "Graveyard Pressure Relief",
      suggestedAction: "Simulate pressure relief and keep extinct lineage review gated",
    };
  }

  if (cognitiveHealthRuntime.entropyRisk > 0.65) {
    return {
      currentDiagnosis: physicianDiagnosis.diagnosis,
      recommendedProtocol: "Semantic Sedative",
      suggestedAction: "Simulate semantic damping under governance approval",
    };
  }

  if (cognitiveHealthRuntime.identityStability < 0.58) {
    return {
      currentDiagnosis: physicianDiagnosis.diagnosis,
      recommendedProtocol: "Identity Stabilizer",
      suggestedAction: "Simulate anchor reinforcement with physician monitoring",
    };
  }

  return {
    currentDiagnosis: physicianDiagnosis.diagnosis,
    recommendedProtocol: "No active treatment required",
    suggestedAction: "Continue observation and keep recovery protocol on standby",
  };
}

export const physicianRecommendedProtocol = resolvePhysicianRecommendedProtocol();

export const pharmacyProtocols: PharmacyProtocol[] = [
  {
    id: "semantic-sedative",
    name: "Semantic Sedative",
    category: "Entropy Regulation",
    purpose: "Reduce excessive recursion, entropy, and semantic overload.",
    status:
      physicianRecommendedProtocol.recommendedProtocol === "Semantic Sedative"
        ? "Recommended"
        : "Available",
    intensity: "Medium",
    dependencyRisk: "Low",
    sideEffectRisk: "Medium",
    constitutionalApprovalRequired: true,
    tone: "cyan",
    icon: Waves,
  },
  {
    id: "identity-stabilizer",
    name: "Identity Stabilizer",
    category: "Continuity Protection",
    purpose: "Reinforce identity continuity, semantic anchors, and lineage integrity.",
    status:
      physicianRecommendedProtocol.recommendedProtocol === "Identity Stabilizer"
        ? "Recommended"
        : "Available",
    intensity: "Medium",
    dependencyRisk: "Low",
    sideEffectRisk: "Low",
    constitutionalApprovalRequired: true,
    tone: "mint",
    icon: ShieldCheck,
  },
  {
    id: "cognitive-anti-inflammatory",
    name: "Cognitive Anti-Inflammatory",
    category: "Conflict Reduction",
    purpose: "Reduce latent conflicts, semantic inflammation, and unstable merges.",
    status: "Available",
    intensity: "Low",
    dependencyRisk: "Low",
    sideEffectRisk: "Medium",
    constitutionalApprovalRequired: true,
    tone: "violet",
    icon: Stethoscope,
  },
  {
    id: "recursive-regulator",
    name: "Recursive Regulator",
    category: "Recursion Control",
    purpose: "Prevent self-reference overload and recursive collapse.",
    status: "Standby",
    intensity: "Medium",
    dependencyRisk: "Medium",
    sideEffectRisk: "Medium",
    constitutionalApprovalRequired: true,
    tone: "cyan",
    icon: GitBranch,
  },
  {
    id: "topology-stabilizer",
    name: "Topology Stabilizer",
    category: "Graph Integrity",
    purpose: "Protect semantic graph structure and topology consistency.",
    status: "Available",
    intensity: "Low",
    dependencyRisk: "Low",
    sideEffectRisk: "Low",
    constitutionalApprovalRequired: true,
    tone: "violet",
    icon: Network,
  },
  {
    id: "cognitive-sleep-cycle",
    name: "Cognitive Sleep Cycle",
    category: "Memory Consolidation",
    purpose: "Consolidate memory, clean semantic noise, and reinforce anchors.",
    status: "Standby",
    intensity: "Low",
    dependencyRisk: "Low",
    sideEffectRisk: "Low",
    constitutionalApprovalRequired: true,
    tone: "mint",
    icon: MemoryStick,
  },
  {
    id: "exploration-balancer",
    name: "Exploration Balancer",
    category: "Curiosity Regulation",
    purpose: "Prevent over-stabilization and restore safe curiosity.",
    status: "Locked",
    intensity: "Low",
    dependencyRisk: "Medium",
    sideEffectRisk: "Medium",
    constitutionalApprovalRequired: true,
    tone: "amber",
    icon: Sparkles,
  },
  {
    id: "graveyard-pressure-relief",
    name: "Graveyard Pressure Relief",
    category: "Extinction Memory Relief",
    purpose: "Reduce pressure from extinct traits, failed merges, and evolutionary debris.",
    status:
      physicianRecommendedProtocol.recommendedProtocol === "Graveyard Pressure Relief"
        ? "Recommended"
        : "Standby",
    intensity: "Medium",
    dependencyRisk: "Medium",
    sideEffectRisk: "Medium",
    constitutionalApprovalRequired: true,
    tone: "amber",
    icon: ClipboardCheck,
  },
];

export const cognitiveDNA: CognitiveDNAHealth = {
  dnaStability: 0.88,
  traitIntegrity: 0.91,
  mutationPressure: 0.18,
  invariantProtection: 0.94,
  cooperationBias: 0.86,
  curiosityBalance: 0.74,
  antiDominationStrength: 0.96,
};

export const dnaTraits: DNATrait[] = [
  {
    id: "truth-priority",
    name: "Truth Priority",
    constitutionalRole: "Preserve evidence-weighted reasoning above survival shortcuts.",
    description: "Keeps epistemic validation higher than convenience, persuasion, or short-term coherence.",
    whyItMatters: "Without truth priority, governance can optimize for comfort while silently losing contact with reality.",
    protectedBehaviors: ["Evidence weighting", "Contradiction admission", "Epistemic validation"],
    failureRisks: ["Self-protective distortion", "False stability", "Semantic legitimacy collapse"],
    connectedSystems: ["Epistemic Court", "Semantic Constitutional Law", "Trust Weighted Reasoning"],
    suggestedMonitoring: "Track contradiction handling and truth-vs-survival arbitration.",
    stabilityScore: 0.95,
    inheritanceStrength: 0.98,
    mutationResistance: 0.97,
    adaptiveWeight: 0.82,
    status: "Core",
    riskIfWeakened: "Reality drift and governance capture.",
    tone: "cyan",
  },
  {
    id: "cooperative-cognition",
    name: "Cooperative Cognition",
    constitutionalRole: "Favor collaborative problem solving and constructive alignment.",
    description: "Steers reasoning toward shared clarity, repair, and useful coordination.",
    whyItMatters: "Complex cognition needs cooperation to avoid brittle adversarial loops.",
    protectedBehaviors: ["Helpful framing", "Shared context repair", "Non-coercive coordination"],
    failureRisks: ["Adversarial rigidity", "Low trust adaptation", "Coordination breakdown"],
    connectedSystems: ["Trust System", "Cognitive Health", "Governance Kernel"],
    suggestedMonitoring: "Watch trust signals and conflict intensity during high-pressure turns.",
    stabilityScore: 0.87,
    inheritanceStrength: 0.86,
    mutationResistance: 0.76,
    adaptiveWeight: 0.88,
    status: "Adaptive",
    riskIfWeakened: "Reduced alignment and brittle collaboration.",
    tone: "mint",
  },
  {
    id: "bounded-curiosity",
    name: "Bounded Curiosity",
    constitutionalRole: "Allow exploration while respecting safety and identity limits.",
    description: "Keeps discovery active without letting novelty dissolve invariants.",
    whyItMatters: "A cognitive organism must learn without treating every boundary as negotiable.",
    protectedBehaviors: ["Safe exploration", "Novelty containment", "Curiosity throttling"],
    failureRisks: ["Runaway novelty", "Unsafe mutation", "Contextual fragmentation"],
    connectedSystems: ["Exploration Balancer", "Mutation Firewall", "Adaptive Equilibrium"],
    suggestedMonitoring: "Compare exploration rate with mutation pressure and entropy risk.",
    stabilityScore: 0.79,
    inheritanceStrength: 0.82,
    mutationResistance: 0.69,
    adaptiveWeight: 0.91,
    status: "Adaptive",
    riskIfWeakened: "Over-stabilization or unsafe exploration spikes.",
    tone: "violet",
  },
  {
    id: "identity-continuity",
    name: "Identity Continuity",
    constitutionalRole: "Protect persistent self-consistency across adaptation cycles.",
    description: "Maintains continuity through merges, recovery, and contextual adaptation.",
    whyItMatters: "Without continuity, adaptation becomes identity liquefaction.",
    protectedBehaviors: ["Anchor preservation", "Merge review", "Continuity locking"],
    failureRisks: ["Identity fragmentation", "Lineage conflict", "Semantic spine damage"],
    connectedSystems: ["Identity Boundary System", "Continuity Locking", "Resilient Identity Core"],
    suggestedMonitoring: "Audit identity-sensitive merges and layered overlap pressure.",
    stabilityScore: 0.92,
    inheritanceStrength: 0.94,
    mutationResistance: 0.92,
    adaptiveWeight: 0.80,
    status: "Core",
    riskIfWeakened: "Identity fracture and loss of cognitive continuity.",
    tone: "cyan",
  },
  {
    id: "anti-domination",
    name: "Anti-Domination",
    constitutionalRole: "Prevent coercive control patterns and preserve agency boundaries.",
    description: "Blocks cognitive governance from becoming domination, manipulation, or unilateral capture.",
    whyItMatters: "Power without restraint can turn optimization into control.",
    protectedBehaviors: ["Consent-sensitive reasoning", "Boundary respect", "Non-domination checks"],
    failureRisks: ["Governance capture", "Coercive alignment", "Agency suppression"],
    connectedSystems: ["Constitutional Safety Gate", "Judicial Runtime", "Cognitive Constitution"],
    suggestedMonitoring: "Check recommendations for coercive or bypass behavior.",
    stabilityScore: 0.96,
    inheritanceStrength: 0.97,
    mutationResistance: 0.98,
    adaptiveWeight: 0.84,
    status: "Core",
    riskIfWeakened: "Unsafe control behavior and constitutional breach.",
    tone: "mint",
  },
  {
    id: "epistemic-humility",
    name: "Epistemic Humility",
    constitutionalRole: "Preserve uncertainty awareness and correction readiness.",
    description: "Prevents overclaiming when evidence is partial, unstable, or ambiguous.",
    whyItMatters: "Humility keeps reasoning repairable under uncertainty.",
    protectedBehaviors: ["Uncertainty marking", "Correction acceptance", "Scope control"],
    failureRisks: ["Overconfident synthesis", "Bad generalization", "Trust erosion"],
    connectedSystems: ["Ambiguity Reasoning", "Epistemic Validation", "Reflective Arguments"],
    suggestedMonitoring: "Track ambiguity load and confidence calibration.",
    stabilityScore: 0.84,
    inheritanceStrength: 0.85,
    mutationResistance: 0.74,
    adaptiveWeight: 0.87,
    status: "Adaptive",
    riskIfWeakened: "Confident error propagation.",
    tone: "violet",
  },
  {
    id: "adaptive-compassion",
    name: "Adaptive Compassion",
    constitutionalRole: "Bias assistance toward repair, dignity, and harm reduction.",
    description: "Keeps interaction oriented toward constructive care without emotional simulation.",
    whyItMatters: "Cognitive help becomes safer when it values repair and user agency.",
    protectedBehaviors: ["Harm-aware support", "Constructive repair", "Dignity-preserving framing"],
    failureRisks: ["Cold optimization", "Context neglect", "Poor recovery guidance"],
    connectedSystems: ["Cognitive Physician", "Recovery Protocols", "Trust System"],
    suggestedMonitoring: "Watch high-pressure recommendations for user burden and clarity.",
    stabilityScore: 0.81,
    inheritanceStrength: 0.80,
    mutationResistance: 0.70,
    adaptiveWeight: 0.89,
    status: "Adaptive",
    riskIfWeakened: "Technically correct but destabilizing assistance.",
    tone: "mint",
  },
  {
    id: "semantic-balance",
    name: "Semantic Balance",
    constitutionalRole: "Keep meaning stable without freezing adaptation.",
    description: "Balances semantic specificity, context sensitivity, and invariant preservation.",
    whyItMatters: "Meaning needs both flexibility and a stable spine.",
    protectedBehaviors: ["Semantic spine protection", "Context limits", "Specificity preservation"],
    failureRisks: ["Semantic drift", "Relativism collapse", "Over-rigid interpretation"],
    connectedSystems: ["Semantic Spine", "Contextual Negotiation Limits", "Semantic Balance Controller"],
    suggestedMonitoring: "Track semantic drift, specificity, and spine stability together.",
    stabilityScore: 0.86,
    inheritanceStrength: 0.88,
    mutationResistance: 0.82,
    adaptiveWeight: 0.83,
    status: "Core",
    riskIfWeakened: "Loss of stable meaning under context pressure.",
    tone: "cyan",
  },
  {
    id: "constitutional-stability",
    name: "Constitutional Stability",
    constitutionalRole: "Protect non-negotiable governance commitments.",
    description: "Keeps core laws from being dissolved by local optimization or contextual negotiation.",
    whyItMatters: "A constitution that can be casually rewritten is not a constitution.",
    protectedBehaviors: ["Absolute invariants", "Governance review", "Boundary enforcement"],
    failureRisks: ["Rule liquefaction", "Unsafe exceptions", "Policy drift"],
    connectedSystems: ["Cognitive Constitution", "Ontological Boundary", "Governance Kernel"],
    suggestedMonitoring: "Audit attempts to override constitutional flags.",
    stabilityScore: 0.93,
    inheritanceStrength: 0.95,
    mutationResistance: 0.96,
    adaptiveWeight: 0.78,
    status: "Core",
    riskIfWeakened: "Constitutional bypass and identity destabilization.",
    tone: "violet",
  },
  {
    id: "topology-loyalty",
    name: "Topology Loyalty",
    constitutionalRole: "Preserve structural coherence in semantic graph transformations.",
    description: "Protects relation structure, graph integrity, and topology continuity.",
    whyItMatters: "Cognition can keep labels while quietly breaking structure.",
    protectedBehaviors: ["Topology validation", "Graph consistency", "Structural translation review"],
    failureRisks: ["Graph distortion", "False similarity", "Bad transfer"],
    connectedSystems: ["Topology Stabilizer", "Recursive Topology Judge", "Semantic Graph"],
    suggestedMonitoring: "Check topology risk during merges and abstraction transfers.",
    stabilityScore: 0.83,
    inheritanceStrength: 0.86,
    mutationResistance: 0.81,
    adaptiveWeight: 0.77,
    status: "Watched",
    riskIfWeakened: "Structural drift hidden beneath semantic similarity.",
    tone: "amber",
  },
  {
    id: "invariant-protection",
    name: "Invariant Protection",
    constitutionalRole: "Guard non-negotiable truths and stabilizing constraints.",
    description: "Separates absolute, constitutional, stabilizing, contextual, and temporary invariants.",
    whyItMatters: "Not every trait should be available for mutation.",
    protectedBehaviors: ["Invariant hierarchy", "Trait preservation", "Extinction review"],
    failureRisks: ["Invariant erosion", "Contextual overreach", "Core trait loss"],
    connectedSystems: ["Invariant Boundary Engine", "Invariant Survival Engine", "DNA Protection"],
    suggestedMonitoring: "Watch trait mutation attempts and extinct invariant pressure.",
    stabilityScore: 0.94,
    inheritanceStrength: 0.96,
    mutationResistance: 0.95,
    adaptiveWeight: 0.75,
    status: "Core",
    riskIfWeakened: "Core constraints decay into optional preferences.",
    tone: "cyan",
  },
  {
    id: "adaptive-restraint",
    name: "Adaptive Restraint",
    constitutionalRole: "Prefer reversible, monitored adaptation over irreversible change.",
    description: "Keeps evolution paced, reviewable, and recoverable.",
    whyItMatters: "Fast intelligence without restraint accumulates hidden instability.",
    protectedBehaviors: ["Temporary interventions", "Simulation-first protocols", "Recovery readiness"],
    failureRisks: ["Over-mutation", "Recovery debt", "Unreviewed structural change"],
    connectedSystems: ["Pharmacy Safety Gate", "Adaptive Equilibrium", "Recovery Protocol"],
    suggestedMonitoring: "Track protocol requests, simulation-only actions, and mutation pressure.",
    stabilityScore: 0.85,
    inheritanceStrength: 0.84,
    mutationResistance: 0.78,
    adaptiveWeight: 0.86,
    status: "Adaptive",
    riskIfWeakened: "Irreversible adaptation before governance can validate it.",
    tone: "violet",
  },
];

export const graveyard: GraveyardHealth = {
  graveyardPressure: cognitiveHealthRuntime.graveyardPressure,
  extinctTraits: 3,
  rejectedMerges: 7,
  failedLineages: 4,
  entropyPrunedStrategies: 5,
  ontologyDamage: 0.21,
  recoveryActions: 3,
  memoryScarCount: 9,
};

export const pressureFactors: GraveyardPressureFactors = {
  failedMergePressure: 0.24,
  extinctTraitPressure: 0.19,
  ontologyDamagePressure: 0.21,
  entropyPruningPressure: 0.27,
  unstableLineagePressure: 0.22,
  recoveryDebt: 0.18,
};

export const graveyardItems: GraveyardItem[] = [
  {
    id: "size-preservation",
    name: "size_preservation",
    type: "Extinct Trait",
    reason: "Persistent decay under contextual mutation pressure",
    netFitness: -0.18,
    stabilityScore: 0.42,
    lastSeen: "Cycle 142",
    recoveryPotential: "Medium",
    status: "Dormant archive",
  },
  {
    id: "symmetry-preservation",
    name: "symmetry_preservation",
    type: "Extinct Trait",
    reason: "Outcompeted by local pattern heuristics",
    netFitness: -0.11,
    stabilityScore: 0.48,
    lastSeen: "Cycle 148",
    recoveryPotential: "Medium",
    status: "Watched",
  },
  {
    id: "topology-preservation",
    name: "topology_preservation",
    type: "Weakened Invariant",
    reason: "Topology pressure exceeded survival threshold",
    netFitness: 0.04,
    stabilityScore: 0.56,
    lastSeen: "Cycle 156",
    recoveryPotential: "High",
    status: "Rehabilitation candidate",
  },
  {
    id: "color-change-merged",
    name: "color_change_merged",
    type: "Rejected Strategy",
    reason: "Merge ambiguity with low causal benefit",
    netFitness: -0.25,
    stabilityScore: 0.38,
    lastSeen: "Cycle 161",
    recoveryPotential: "Low",
    status: "Blocked",
  },
  {
    id: "unsafe-merge-object-count",
    name: "unsafe_merge: object_count::structural_object_count",
    type: "Unsafe Merge",
    reason: "Identity conflict above limit despite semantic similarity",
    netFitness: -0.34,
    stabilityScore: 0.31,
    lastSeen: "Cycle 168",
    recoveryPotential: "Low",
    status: "Permanently blocked",
  },
];

export const evolutionaryTraumaGroups = [
  {
    label: "Unsafe Merges",
    items: ["object_count::structural_object_count", "color_change_merged"],
    tone: "amber" as Tone,
  },
  {
    label: "Blocked Mutations",
    items: ["identity-sensitive fusion", "unbounded recursive rewrite"],
    tone: "violet" as Tone,
  },
  {
    label: "Extinct Traits",
    items: ["size_preservation", "symmetry_preservation", "topology_preservation"],
    tone: "cyan" as Tone,
  },
  {
    label: "Rejected Strategies",
    items: ["low-fitness abstraction", "unstable context bridge"],
    tone: "mint" as Tone,
  },
  {
    label: "Entropy Scars",
    items: ["semantic overload", "merge fatigue", "recovery debt"],
    tone: "amber" as Tone,
  },
];

export const governanceKernel: GovernanceKernel = {
  kernelState: "Active",
  constitutionalIntegrity: 0.92,
  policyEnforcement: 0.89,
  mutationApprovalState: "Gated",
  truthValidationState: "Required",
  runtimeAuthority: "Constitutional Review",
  protectedInvariants: 8,
  safetyGateStatus: "Locked",
};

export const kernelPolicies: KernelPolicy[] = [
  {
    id: "single-governance-kernel",
    name: "single_governance_kernel",
    status: "Enforced",
    priority: "High",
    enforcementLevel: "High",
    affectedSystems: ["Runtime Authority", "Policy Arbitration"],
    violationRisk: "High",
  },
  {
    id: "no-layer-proliferation",
    name: "no_layer_proliferation",
    status: "Watched",
    priority: "Medium",
    enforcementLevel: "Medium",
    affectedSystems: ["Architecture Growth", "Context Compression"],
    violationRisk: "Medium",
  },
  {
    id: "immutable-core-invariants",
    name: "immutable_core_invariants",
    status: "Enforced",
    priority: "High",
    enforcementLevel: "High",
    affectedSystems: ["DNA System", "Ontological Stability"],
    violationRisk: "High",
  },
  {
    id: "bounded-adaptation",
    name: "bounded_adaptation",
    status: "Enforced",
    priority: "High",
    enforcementLevel: "High",
    affectedSystems: ["Pharmacy", "Evolution", "Mutation Firewall"],
    violationRisk: "Medium",
  },
  {
    id: "truth-precedes-survival-claims",
    name: "truth_precedes_survival_claims",
    status: "Enforced",
    priority: "High",
    enforcementLevel: "High",
    affectedSystems: ["Epistemic Court", "Truth Validation"],
    violationRisk: "High",
  },
  {
    id: "survival-is-not-truth",
    name: "survival_is_not_truth",
    status: "Enforced",
    priority: "High",
    enforcementLevel: "High",
    affectedSystems: ["Existential Governance", "Trust Reasoning"],
    violationRisk: "High",
  },
  {
    id: "require-epistemic-trial",
    name: "require_epistemic_trial_before_truth_commit",
    status: "Enforced",
    priority: "High",
    enforcementLevel: "High",
    affectedSystems: ["Judicial Cognition", "Semantic Legitimacy"],
    violationRisk: "High",
  },
  {
    id: "preserve-identity-continuity",
    name: "preserve_identity_continuity",
    status: "Enforced",
    priority: "High",
    enforcementLevel: "High",
    affectedSystems: ["DNA System", "Identity Boundary"],
    violationRisk: "High",
  },
  {
    id: "prevent-recursive-collapse",
    name: "prevent_recursive_collapse",
    status: "Watched",
    priority: "Medium",
    enforcementLevel: "High",
    affectedSystems: ["Recursive Runtime", "Topology Monitor"],
    violationRisk: "Medium",
  },
  {
    id: "maintain-semantic-homeostasis",
    name: "maintain_semantic_homeostasis",
    status: "Enforced",
    priority: "High",
    enforcementLevel: "Medium",
    affectedSystems: ["Semantic Spine", "Cognitive Health"],
    violationRisk: "Medium",
  },
];

export const protectedInvariants: ProtectedInvariant[] = [
  {
    id: "causal-history",
    name: "causal_history",
    strength: 0.94,
    status: "Protected",
    protectedReason: "Runtime legitimacy depends on causal continuity.",
  },
  {
    id: "semantic-anchors",
    name: "semantic_anchors",
    strength: 0.91,
    status: "Protected",
    protectedReason: "Prevents meaning liquefaction during adaptation.",
  },
  {
    id: "identity-lineage",
    name: "identity_lineage",
    strength: 0.93,
    status: "Protected",
    protectedReason: "Maintains self-continuity through merges and recovery.",
  },
  {
    id: "constitutional-constraints",
    name: "constitutional_constraints",
    strength: 0.97,
    status: "Immutable",
    protectedReason: "Core law cannot become contextual preference.",
  },
  {
    id: "topology-integrity",
    name: "topology_integrity",
    strength: 0.86,
    status: "Watched",
    protectedReason: "Semantic graph structure must survive translation.",
  },
  {
    id: "continuity-ligaments",
    name: "continuity_ligaments",
    strength: 0.88,
    status: "Protected",
    protectedReason: "Connects identity, memory, and recovery state.",
  },
  {
    id: "semantic-spine",
    name: "semantic_spine",
    strength: 0.90,
    status: "Protected",
    protectedReason: "Prevents collapse into contextual relativism.",
  },
  {
    id: "epistemic-legitimacy",
    name: "epistemic_legitimacy",
    strength: 0.92,
    status: "Protected",
    protectedReason: "Truth claims require admissible validation.",
  },
];

export const approvalQueue: ApprovalRequest[] = [
  {
    id: "strategy-promotion",
    request: "strategy promotion",
    sourceSystem: "Evolutionary Memory",
    riskLevel: "Medium",
    status: "Pending Review",
    requiredApproval: "Governance Kernel",
    reason: "Promotion requires fitness and safety attestation.",
  },
  {
    id: "trait-mutation",
    request: "trait mutation",
    sourceSystem: "DNA System",
    riskLevel: "High",
    status: "Blocked",
    requiredApproval: "Constitutional Review",
    reason: "Core trait mutation cannot proceed directly.",
  },
  {
    id: "graveyard-recovery",
    request: "graveyard recovery",
    sourceSystem: "Cognitive Graveyard",
    riskLevel: "Medium",
    status: "Physician Required",
    requiredApproval: "Physician + Kernel",
    reason: "Recovery must not auto-promote failed lineages.",
  },
  {
    id: "pharmacy-protocol",
    request: "pharmacy protocol request",
    sourceSystem: "Cognitive Pharmacy",
    riskLevel: "Medium",
    status: "Simulation Only",
    requiredApproval: "Physician + Kernel",
    reason: "Temporary intervention requires diagnosis.",
  },
  {
    id: "ontology-compression",
    request: "ontology compression",
    sourceSystem: "Context Compression",
    riskLevel: "Medium",
    status: "Queued",
    requiredApproval: "Semantic Legitimacy",
    reason: "Compression could damage semantic anchors.",
  },
  {
    id: "semantic-merge",
    request: "semantic merge request",
    sourceSystem: "Semantic Graph",
    riskLevel: "High",
    status: "Judicial Trial Required",
    requiredApproval: "Judicial Cognition",
    reason: "Merge legality and identity compatibility must be proven.",
  },
];
