# Architecture Quality Attribute Dataset

## Purpose

This dataset supports supervised multi-label classification of
Architecturally Significant Requirements (ASRs) into software quality
attributes for the DesignTrace AI Architecture Decision Agent.

## Supported Quality Attributes

The current research scope contains six quality attributes:

1. Security
2. Scalability
3. Performance
4. Reliability
5. Maintainability
6. Availability

A requirement may belong to one or more quality attributes.

## Dataset Status

The dataset is currently a synthetic, developer-assisted research dataset.

The examples were constructed to represent realistic software requirements
across several application domains. They must not be treated as independently
expert-validated ground truth at the current stage.

Expert review and larger external validation are planned for a later research
milestone.

## Domains

Examples include requirements from domains such as:

- Healthcare
- Banking
- E-commerce
- IoT
- Education
- Logistics
- Human Resources
- Telecommunications
- Cloud systems
- Government systems
- Transportation
- Social media
- Enterprise systems

## Record Format

```json
{
  "example_id": "QA-0001",
  "statement": "Only authorised clinical personnel may access patient diagnostic history.",
  "labels": ["Security"],
  "source_type": "synthetic",
  "domain": "healthcare"
}