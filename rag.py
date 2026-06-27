"""
Lightweight RAG Engine for SOLARIS
Uses TF-IDF + cosine similarity (no external vector DB needed for hackathon)
For production: swap with Azure Cognitive Search or pgvector
"""

import math
import re
from typing import List, Tuple


ENTERPRISE_STANDARDS = [
    {
        "id": "sec-001",
        "category": "Security",
        "title": "Zero Trust Architecture",
        "content": """Zero Trust security model: never trust, always verify. 
        All users, devices, and network traffic must be authenticated and authorized.
        Implement: Identity-based access (IAM), micro-segmentation, least privilege,
        continuous monitoring, MFA for all services. Applicable standards: NIST SP 800-207.
        Required for all internet-facing and internal enterprise systems.""",
        "tags": ["security", "zero-trust", "IAM", "authentication", "NIST"]
    },
    {
        "id": "sec-002",
        "category": "Security",
        "title": "GDPR Data Protection Requirements",
        "content": """GDPR Compliance for architecture: Data minimization principle - collect only necessary data.
        PII must be encrypted at rest (AES-256) and in transit (TLS 1.3+).
        Data residency: EU data must stay in EU regions. Implement data lineage tracking.
        Right to erasure requires soft-delete patterns. Consent management required.
        Data retention policies must be enforced. DPO notification within 72hrs of breach.
        Architecture must include: encryption, audit logs, anonymization, consent store.""",
        "tags": ["GDPR", "compliance", "privacy", "PII", "encryption", "EU"]
    },
    {
        "id": "arch-001",
        "category": "Architecture Pattern",
        "title": "Microservices Reference Architecture",
        "content": """Enterprise microservices pattern: Services should be independently deployable.
        API Gateway for ingress (rate limiting, auth, routing). Service mesh (Istio/Linkerd) for 
        service-to-service communication. Each service owns its database (database per service pattern).
        Async communication via message broker (Kafka/RabbitMQ) for eventual consistency.
        Circuit breaker pattern (Resilience4j) for fault tolerance. Distributed tracing (Jaeger/Zipkin).
        Container orchestration: Kubernetes. Sidecar pattern for cross-cutting concerns.
        Anti-pattern: shared database across services (creates tight coupling).""",
        "tags": ["microservices", "kubernetes", "API gateway", "kafka", "service mesh"]
    },
    {
        "id": "arch-002",
        "category": "Architecture Pattern",
        "title": "Event-Driven Architecture",
        "content": """Event-driven architecture (EDA) reference pattern. Use when: high throughput, 
        loose coupling, async workflows needed. Core components: Event producers, Event broker (Kafka/Azure Service Bus),
        Event consumers, Event store. Patterns: Event sourcing (audit trail), CQRS (read/write separation),
        Saga pattern (distributed transactions). Benefits: scalability, resilience, auditability.
        Risks: eventual consistency complexity, message ordering, idempotency requirements.
        Dead letter queues mandatory for failed event handling.""",
        "tags": ["event-driven", "kafka", "CQRS", "event sourcing", "saga", "async"]
    },
    {
        "id": "cloud-001",
        "category": "Cloud Standards",
        "title": "Azure Well-Architected Framework",
        "content": """Azure Well-Architected 5 pillars: Reliability (SLA >99.9%, multi-region, chaos engineering),
        Security (Azure AD, Key Vault, Defender for Cloud, private endpoints),
        Cost Optimization (reserved instances, auto-scaling, right-sizing, budgets),
        Operational Excellence (IaC with Bicep/Terraform, CI/CD, monitoring with Azure Monitor),
        Performance Efficiency (caching Redis, CDN, horizontal scaling, load testing).
        Mandatory: Tag resources for cost allocation. Use Azure Advisor recommendations.
        Avoid: public endpoints without WAF, unencrypted storage, over-provisioned VMs.""",
        "tags": ["azure", "well-architected", "reliability", "cost", "security", "cloud"]
    },
    {
        "id": "cloud-002",
        "category": "Cloud Standards",
        "title": "Multi-Cloud and Vendor Lock-in Prevention",
        "content": """Vendor lock-in risk mitigation: Use open standards (Kubernetes, OpenTelemetry, CloudEvents).
        Abstract cloud-specific services behind adapters/facades. 
        Avoid: proprietary ML services without abstraction, cloud-specific message formats.
        Use: Terraform for infra (cloud-agnostic), standard SQL where possible, 
        container images (portable). Assess lock-in risk: Low (compute/storage), 
        Medium (managed databases), High (serverless, proprietary AI/ML services).
        Architecture reviews must include vendor dependency scoring.""",
        "tags": ["vendor lock-in", "multi-cloud", "terraform", "kubernetes", "portability"]
    },
    {
        "id": "nfr-001",
        "category": "NFR",
        "title": "Scalability and Performance NFRs",
        "content": """Standard NFR targets: Availability SLA 99.9% (8.7h/yr downtime), 99.99% for critical.
        Response time: API <200ms p95, UI <3s page load. Throughput: define peak TPS with 3x headroom.
        Horizontal scaling preferred over vertical. Auto-scaling based on CPU >70%, memory >80%.
        Database: read replicas for read-heavy workloads, connection pooling mandatory.
        Caching: CDN for static assets, Redis for session/computation cache.
        Performance testing: baseline, load, stress, soak tests required pre-production.
        Capacity planning: 18-month forecast required for approval.""",
        "tags": ["scalability", "performance", "SLA", "availability", "NFR", "auto-scaling"]
    },
    {
        "id": "nfr-002",
        "category": "NFR",
        "title": "Observability and Monitoring Standards",
        "content": """Observability three pillars: Metrics, Logs, Traces. All services must emit:
        RED metrics (Rate, Errors, Duration). Structured JSON logging mandatory (no plain text).
        Distributed tracing: correlation ID propagated across all service calls.
        Alerting: PagerDuty integration, SLO-based alerting (error budget).
        Dashboards: service health, business KPIs, infrastructure metrics.
        Log retention: 90 days hot, 1 year cold (compliance). 
        Anomaly detection via AI ops (Azure Monitor / Dynatrace).
        On-call runbooks required for every alert. MTTR target: <30 mins.""",
        "tags": ["observability", "monitoring", "logging", "tracing", "SLO", "alerting"]
    },
    {
        "id": "data-001",
        "category": "Data Architecture",
        "title": "Data Mesh and Modern Data Architecture",
        "content": """Data mesh principles: Domain-oriented ownership, data as product, self-serve infrastructure,
        federated governance. Data platform layers: Ingestion (Kafka/ADF), Storage (Data Lake Gen2),
        Processing (Databricks/Synapse), Serving (Synapse SQL, Power BI).
        Medallion architecture: Bronze (raw), Silver (cleansed), Gold (business-ready).
        Data cataloging mandatory (Purview/DataHub). Column-level lineage for PII.
        API-first data sharing. Avoid: central monolithic data warehouse for new projects.
        ML feature store for ML workloads. Real-time + batch processing (Lambda/Kappa architecture).""",
        "tags": ["data mesh", "data lake", "databricks", "ML", "data catalog", "medallion"]
    },
    {
        "id": "sec-003",
        "category": "Security",
        "title": "API Security Standards",
        "content": """API security checklist: OAuth 2.0 + OIDC for authentication. JWT tokens (short-lived, <15min).
        API keys for machine-to-machine (rotate every 90 days). Rate limiting per client.
        Input validation: reject unexpected fields, sanitize all inputs. 
        OWASP API Top 10 must be addressed: Broken Object Level Authorization, 
        Broken Authentication, Excessive Data Exposure, Lack of Resources & Rate Limiting.
        mTLS for service-to-service. API versioning strategy required (URI or header).
        Never expose internal IDs directly. Audit log all API calls with user context.""",
        "tags": ["API security", "OAuth", "JWT", "OWASP", "rate limiting", "authentication"]
    }
]


class RAGEngine:
    """Simple TF-IDF based RAG - no external dependencies needed"""

    def __init__(self):
        self.documents = ENTERPRISE_STANDARDS
        self._build_index()

    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenizer"""
        text = text.lower()
        tokens = re.findall(r'\b[a-z][a-z0-9\-]*\b', text)
        stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                     'for', 'with', 'this', 'that', 'and', 'or', 'in', 'on', 'at',
                     'to', 'of', 'it', 'its', 'by', 'as', 'all', 'must', 'should'}
        return [t for t in tokens if t not in stopwords and len(t) > 2]

    def _build_index(self):
        """Build TF-IDF index"""
        self.doc_tokens = []
        for doc in self.documents:
            text = f"{doc['title']} {doc['content']} {' '.join(doc['tags'])}"
            self.doc_tokens.append(self._tokenize(text))

        # Build vocabulary
        all_tokens = set()
        for tokens in self.doc_tokens:
            all_tokens.update(tokens)
        self.vocab = list(all_tokens)
        self.vocab_idx = {t: i for i, t in enumerate(self.vocab)}

        # Compute IDF
        N = len(self.documents)
        self.idf = {}
        for term in self.vocab:
            df = sum(1 for tokens in self.doc_tokens if term in tokens)
            self.idf[term] = math.log((N + 1) / (df + 1)) + 1

        # Compute TF-IDF vectors
        self.doc_vectors = []
        for tokens in self.doc_tokens:
            tf = {}
            for t in tokens:
                tf[t] = tf.get(t, 0) + 1
            vec = {}
            for t, count in tf.items():
                vec[t] = (count / len(tokens)) * self.idf.get(t, 1)
            self.doc_vectors.append(vec)

    def _cosine_sim(self, vec1: dict, vec2: dict) -> float:
        common = set(vec1.keys()) & set(vec2.keys())
        if not common:
            return 0.0
        dot = sum(vec1[t] * vec2[t] for t in common)
        mag1 = math.sqrt(sum(v ** 2 for v in vec1.values()))
        mag2 = math.sqrt(sum(v ** 2 for v in vec2.values()))
        if mag1 == 0 or mag2 == 0:
            return 0.0
        return dot / (mag1 * mag2)

    def search(self, query: str, top_k: int = 3) -> str:
        """Search and return formatted context string"""
        query_tokens = self._tokenize(query)
        query_vec = {}
        for t in query_tokens:
            query_vec[t] = query_vec.get(t, 0) + (1 * self.idf.get(t, 1))

        scores: List[Tuple[float, int]] = []
        for i, doc_vec in enumerate(self.doc_vectors):
            score = self._cosine_sim(query_vec, doc_vec)
            scores.append((score, i))

        scores.sort(reverse=True)
        top = [(s, i) for s, i in scores[:top_k] if s > 0.05]

        if not top:
            return ""

        parts = []
        for score, idx in top:
            doc = self.documents[idx]
            parts.append(
                f"[{doc['category']}] {doc['title']} (relevance: {score:.2f})\n{doc['content']}"
            )

        return "\n\n---\n\n".join(parts)

    def add_document(self, doc: dict):
        """Add a custom document to the RAG index"""
        self.documents.append(doc)
        self._build_index()
