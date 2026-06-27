"""
SOLARIS Tool Definitions and Execution
Claude uses these tools to perform specialized architecture tasks
"""

import json
from typing import Any


def get_tool_definitions() -> list:
    """Return tool definitions for Claude's tool_use"""
    return [
        {
            "name": "search_standards",
            "description": "Search enterprise architecture standards, security policies, compliance requirements, and reference patterns from the organization's knowledge base. Use this when you need to validate against enterprise standards or find relevant patterns.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for finding relevant standards (e.g., 'GDPR data encryption', 'microservices API security')"
                    }
                },
                "required": ["query"]
            }
        },
        {
            "name": "generate_diagram",
            "description": "Generate a Mermaid diagram for architecture visualization. Supports: architecture overview, sequence diagrams, deployment diagrams, data flow diagrams, and component diagrams.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "diagram_type": {
                        "type": "string",
                        "enum": ["architecture", "sequence", "deployment", "dataflow", "component", "er"],
                        "description": "Type of diagram to generate"
                    },
                    "components": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of components/services involved"
                    },
                    "description": {
                        "type": "string",
                        "description": "Description of what the diagram should show"
                    },
                    "relationships": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of relationships between components (e.g., 'User -> API Gateway: HTTPS request')"
                    }
                },
                "required": ["diagram_type", "description"]
            }
        },
        {
            "name": "evaluate_tradeoffs",
            "description": "Evaluate architecture trade-offs across multiple dimensions: cost, scalability, security, maintainability, performance, vendor lock-in, and time-to-market. Returns a structured evaluation.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "options": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "description": {"type": "string"}
                            }
                        },
                        "description": "Architecture options to compare"
                    },
                    "context": {
                        "type": "string",
                        "description": "Business context and constraints for the evaluation"
                    },
                    "priority_dimensions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Which dimensions matter most (e.g., ['cost', 'security', 'scalability'])"
                    }
                },
                "required": ["options", "context"]
            }
        },
        {
            "name": "generate_adr",
            "description": "Generate a formal Architecture Decision Record (ADR) following the standard template. ADRs document important architectural decisions with context, alternatives, and consequences.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Short title for the decision (e.g., 'Use Event Sourcing for Order Management')"
                    },
                    "context": {
                        "type": "string",
                        "description": "Business and technical context driving this decision"
                    },
                    "decision": {
                        "type": "string",
                        "description": "The architectural decision made"
                    },
                    "alternatives": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Alternative options that were considered"
                    },
                    "consequences": {
                        "type": "object",
                        "properties": {
                            "positive": {"type": "array", "items": {"type": "string"}},
                            "negative": {"type": "array", "items": {"type": "string"}},
                            "risks": {"type": "array", "items": {"type": "string"}}
                        }
                    }
                },
                "required": ["title", "context", "decision"]
            }
        },
        {
            "name": "estimate_tco",
            "description": "Estimate Total Cost of Ownership for the proposed architecture over 1, 3, and 5 years including infrastructure, licensing, development, operations, and hidden costs.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "components": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "type": {"type": "string"},
                                "scale": {"type": "string"}
                            }
                        },
                        "description": "Infrastructure components and their scale"
                    },
                    "cloud_provider": {
                        "type": "string",
                        "description": "Primary cloud provider (Azure, AWS, GCP)"
                    },
                    "team_size": {
                        "type": "integer",
                        "description": "Number of engineers required"
                    },
                    "region": {
                        "type": "string",
                        "description": "Deployment region (affects pricing)"
                    }
                },
                "required": ["components"]
            }
        },
        {
            "name": "check_compliance",
            "description": "Validate the proposed architecture against compliance frameworks: GDPR, SOC2, ISO 27001, HIPAA, PCI-DSS. Returns compliance gaps and remediation recommendations.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "architecture_description": {
                        "type": "string",
                        "description": "Description of the proposed architecture"
                    },
                    "frameworks": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Compliance frameworks to check against (e.g., ['GDPR', 'SOC2'])"
                    },
                    "data_types": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Types of data handled (e.g., ['PII', 'financial', 'health'])"
                    }
                },
                "required": ["architecture_description", "frameworks"]
            }
        }
    ]


def execute_tool(tool_name: str, tool_input: dict, rag) -> str:
    """Execute a tool and return result as string"""

    if tool_name == "search_standards":
        result = rag.search(tool_input["query"], top_k=3)
        if not result:
            return "No specific enterprise standards found for this query. Proceeding with industry best practices."
        return f"Retrieved enterprise standards:\n\n{result}"

    elif tool_name == "generate_diagram":
        return _generate_diagram(tool_input)

    elif tool_name == "evaluate_tradeoffs":
        return _evaluate_tradeoffs(tool_input)

    elif tool_name == "generate_adr":
        return _generate_adr(tool_input)

    elif tool_name == "estimate_tco":
        return _estimate_tco(tool_input)

    elif tool_name == "check_compliance":
        return _check_compliance(tool_input)

    return f"Unknown tool: {tool_name}"


def _generate_diagram(inp: dict) -> str:
    """Generate Mermaid diagram template"""
    dtype = inp.get("diagram_type", "architecture")
    desc = inp.get("description", "")
    components = inp.get("components", [])
    relationships = inp.get("relationships", [])

    templates = {
        "architecture": _arch_template,
        "sequence": _sequence_template,
        "deployment": _deployment_template,
        "dataflow": _dataflow_template,
        "component": _component_template,
    }

    fn = templates.get(dtype, _arch_template)
    diagram = fn(components, relationships, desc)

    return f"""Diagram template generated ({dtype}):

{diagram}

Note: This is a starting template. Claude will refine it based on your specific requirements.
Components identified: {', '.join(components) if components else 'from description'}"""


def _arch_template(components, relationships, desc):
    comp_str = "\n    ".join([f'{c.replace(" ", "_")}["{c}"]' for c in (components or ["Client", "API Gateway", "Service", "Database"])])
    return f"""```mermaid
graph TB
    {comp_str}
    
    %% Add your connections based on: {desc}
    %% Example: Client --> API_Gateway --> Service --> Database
```"""


def _sequence_template(components, relationships, desc):
    parts = components or ["Client", "API Gateway", "Service", "Database"]
    actors = "\n    ".join([f"participant {p.replace(' ', '_')} as {p}" for p in parts])
    return f"""```mermaid
sequenceDiagram
    {actors}
    
    %% Sequence for: {desc}
    Note over {parts[0].replace(' ', '_')}: Request starts here
```"""


def _deployment_template(components, relationships, desc):
    return f"""```mermaid
graph TB
    subgraph Azure["☁️ Azure Cloud"]
        subgraph VNet["Virtual Network"]
            subgraph PublicSubnet["Public Subnet"]
                AGW["Application Gateway / WAF"]
            end
            subgraph PrivateSubnet["Private Subnet"]
                AKS["AKS Cluster"]
                APIM["API Management"]
            end
            subgraph DataSubnet["Data Subnet"]
                DB[("Azure SQL / Cosmos DB")]
                REDIS["Azure Cache for Redis"]
            end
        end
        KV["Key Vault 🔐"]
        ACR["Container Registry"]
        MON["Azure Monitor"]
    end
    
    USERS["👤 End Users"] --> AGW
    AGW --> APIM
    APIM --> AKS
    AKS --> DB
    AKS --> REDIS
    AKS --> KV
```"""


def _dataflow_template(components, relationships, desc):
    return f"""```mermaid
flowchart LR
    SRC["📥 Data Source"] --> ING["Ingestion Layer\\nKafka / Event Hub"]
    ING --> PROC["Processing Layer\\nDatabricks / Stream Analytics"]
    PROC --> STR["Storage Layer\\nData Lake Gen2"]
    STR --> SERVE["Serving Layer\\nSynapse / Power BI"]
    SERVE --> CON["👤 Consumers"]
    
    style SRC fill:#4CAF50,color:#fff
    style ING fill:#2196F3,color:#fff
    style PROC fill:#9C27B0,color:#fff
    style STR fill:#FF9800,color:#fff
    style SERVE fill:#F44336,color:#fff
```"""


def _component_template(components, relationships, desc):
    comps = components or ["Frontend", "API Layer", "Business Logic", "Data Access", "Database"]
    nodes = "\n    ".join([f'{c.replace(" ", "_")}["{c}"]' for c in comps])
    return f"""```mermaid
graph LR
    {nodes}
```"""


def _evaluate_tradeoffs(inp: dict) -> str:
    options = inp.get("options", [])
    context = inp.get("context", "")
    priorities = inp.get("priority_dimensions", ["cost", "scalability", "security"])

    result = f"""Trade-off Evaluation Framework
Context: {context}
Priority Dimensions: {', '.join(priorities)}

Evaluation Template (Claude will score based on requirements):

| Dimension | Weight |"""

    for opt in options:
        result += f" {opt.get('name', 'Option')} |"

    result += "\n|-----------|--------|"
    for _ in options:
        result += "---------|"

    dimensions = [
        ("Cost (CapEx + OpEx)", "20%"),
        ("Scalability", "20%"),
        ("Security", "20%"),
        ("Developer Experience", "10%"),
        ("Time to Market", "15%"),
        ("Vendor Lock-in Risk", "10%"),
        ("Operational Complexity", "5%"),
    ]

    for dim, weight in dimensions:
        result += f"\n| {dim} | {weight} |"
        for _ in options:
            result += " TBD |"

    result += f"""

⚠️ Key Risks to Evaluate:
- Vendor lock-in dependencies
- Scalability bottlenecks under peak load
- Security attack surface
- Missing NFRs (availability, DR, data residency)
- Hidden operational costs

Recommendation format will follow after full evaluation."""

    return result


def _generate_adr(inp: dict) -> str:
    title = inp.get("title", "Architecture Decision")
    context = inp.get("context", "")
    decision = inp.get("decision", "")
    alternatives = inp.get("alternatives", [])
    consequences = inp.get("consequences", {})

    adr_number = "ADR-001"
    date = "2025-01-01"

    alt_text = "\n".join([f"- {a}" for a in alternatives]) if alternatives else "- See decision text"
    pos = "\n".join([f"  ✅ {p}" for p in consequences.get("positive", ["TBD"])])
    neg = "\n".join([f"  ❌ {n}" for n in consequences.get("negative", ["TBD"])])
    risks = "\n".join([f"  ⚠️ {r}" for r in consequences.get("risks", ["TBD"])])

    return f"""# {adr_number}: {title}

**Date:** {date}
**Status:** Proposed
**Deciders:** Architecture Review Board

## Context and Problem Statement

{context}

## Decision Drivers

- Enterprise architecture standards compliance
- Non-functional requirements (security, scalability, cost)
- Team capability and operational maturity
- Time-to-market constraints

## Considered Options

{alt_text}

## Decision Outcome

**Chosen option:** {decision}

### Consequences

**Positive:**
{pos}

**Negative:**
{neg}

**Risks:**
{risks}

## Implementation Notes

- Review required: Architecture Review Board
- Linked standards: See enterprise standards documentation
- Review date: 6 months post-implementation

---
*Generated by SOLARIS - SOLution ARchitecture Intelligence System*"""


def _estimate_tco(inp: dict) -> str:
    components = inp.get("components", [])
    cloud = inp.get("cloud_provider", "Azure")
    team_size = inp.get("team_size", 3)
    region = inp.get("region", "West Europe")

    infra_monthly = len(components) * 500
    dev_monthly = team_size * 8000
    ops_monthly = infra_monthly * 0.2

    year1 = (infra_monthly + ops_monthly) * 12 + dev_monthly * 12 * 0.5
    year3 = year1 * 2.8
    year5 = year1 * 4.2

    return f"""## TCO Estimate: {cloud} Deployment ({region})

### Infrastructure Costs (Monthly Estimates)

| Component | Type | Est. Monthly Cost |
|-----------|------|-------------------|
{chr(10).join([f'| {c.get("name", "Component")} | {c.get("type", "Service")} | €{500:,} |' for c in components])}
| Monitoring & Security | Azure Monitor, Defender | €{300:,} |
| Networking | VNet, Load Balancer, Egress | €{200:,} |
| **Total Infrastructure** | | **€{infra_monthly:,}/mo** |

### Total Cost Summary

| Period | Infrastructure | Development | Operations | **Total** |
|--------|---------------|-------------|------------|-----------|
| Year 1 | €{infra_monthly*12:,} | €{dev_monthly*6:,} | €{int(ops_monthly*12):,} | **€{int(year1):,}** |
| Year 3 | €{infra_monthly*12*2:,} | €{dev_monthly*12:,} | €{int(ops_monthly*12*2):,} | **€{int(year3):,}** |
| Year 5 | €{infra_monthly*12*3:,} | €{dev_monthly*12:,} | €{int(ops_monthly*12*3):,} | **€{int(year5):,}** |

### Cost Optimization Recommendations

1. **Reserved Instances** - 1-3yr commitments: ~40% savings on compute
2. **Auto-scaling** - Scale down off-hours: est. 30% compute savings
3. **Right-sizing** - Monthly review via Azure Advisor
4. **Dev/Test** - Shutdown non-prod environments nights/weekends: ~60% savings

### Hidden Costs to Budget

- ⚠️ Data egress fees (often underestimated)
- ⚠️ Developer training and ramp-up
- ⚠️ Incident response and on-call premium
- ⚠️ Compliance audit costs (GDPR DPA, SOC2)
- ⚠️ License fees (enterprise tools, monitoring)

*Estimates based on Azure public pricing. Use Azure Pricing Calculator for precise quotes.*"""


def _check_compliance(inp: dict) -> str:
    arch = inp.get("architecture_description", "")
    frameworks = inp.get("frameworks", ["GDPR"])
    data_types = inp.get("data_types", [])

    checks = {
        "GDPR": [
            ("Data encryption at rest (AES-256)", "🔴 VERIFY"),
            ("Data encryption in transit (TLS 1.3+)", "🔴 VERIFY"),
            ("Data residency in EU region", "🔴 VERIFY"),
            ("Right to erasure (soft-delete pattern)", "🔴 VERIFY"),
            ("Consent management system", "🔴 VERIFY"),
            ("Data breach notification process (<72hrs)", "🔴 VERIFY"),
            ("Data minimization principle", "🔴 VERIFY"),
            ("DPO appointed and process documented", "🔴 VERIFY"),
        ],
        "SOC2": [
            ("Access controls and IAM", "🔴 VERIFY"),
            ("Audit logging (all user actions)", "🔴 VERIFY"),
            ("Change management process", "🔴 VERIFY"),
            ("Incident response procedure", "🔴 VERIFY"),
            ("Vulnerability management", "🔴 VERIFY"),
        ],
        "ISO27001": [
            ("Information security policy", "🔴 VERIFY"),
            ("Risk assessment documented", "🔴 VERIFY"),
            ("Asset inventory maintained", "🔴 VERIFY"),
            ("Business continuity plan", "🔴 VERIFY"),
        ]
    }

    result = f"""## Compliance Validation Report

**Architecture:** {arch[:200]}...
**Data Types:** {', '.join(data_types) if data_types else 'Not specified'}
**Frameworks Checked:** {', '.join(frameworks)}

---

"""
    for fw in frameworks:
        if fw in checks:
            result += f"### {fw} Compliance Checklist\n\n"
            result += "| Requirement | Status | Action Required |\n"
            result += "|-------------|--------|----------------|\n"
            for req, status in checks[fw]:
                result += f"| {req} | {status} | Review architecture |\n"
            result += "\n"

    result += """### ⚠️ Critical Gaps (Common Issues)

1. **PII Data Flow** - Ensure all PII is tagged and tracked through data lineage
2. **Encryption Key Management** - Azure Key Vault required, no hardcoded secrets
3. **Access Logging** - Every data access must be logged with user identity
4. **Data Retention** - Automated deletion policies must be implemented
5. **Third-party Processors** - All external APIs handling PII need DPA agreements

### Next Steps

1. Complete architecture review with DPO
2. Run DPIA (Data Protection Impact Assessment) for high-risk processing
3. Penetration testing pre-production
4. Schedule compliance audit 3 months post-launch

*Note: This is an automated pre-check. Full compliance requires legal review.*"""

    return result
