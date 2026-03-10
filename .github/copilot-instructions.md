# Rate Limiter - Copilot Instructions

## Repository Overview

This repository is a **documentation-focused project** that provides comprehensive educational content about rate limiting algorithms and their real-world applications. It is NOT a code implementation repository - it focuses on explaining concepts, algorithms, and system design patterns for rate limiting.

**Key Characteristics:**
- Type: Documentation/Educational Resource
- Primary Content: Markdown documentation files
- Purpose: Teaching rate limiting concepts (Token Bucket, Leaky Bucket, Fixed Window, Sliding Window, etc.)
- Target Audience: Developers learning about rate limiting and system design

## Repository Structure

```
Rate-Limiter/
├── README.md              # Main introduction and overview
├── documentation.md       # Comprehensive guide (41KB+) covering algorithms, components, metrics, HTTP headers, and real-world designs
└── .github/
    └── copilot-instructions.md
```

## Content Focus

The repository contains detailed explanations of:

1. **Core Rate Limiting Algorithms:**
   - Token Bucket
   - Leaky Bucket  
   - Fixed Window Counter
   - Sliding Window Log
   - Sliding Window Counter

2. **System Components:**
   - Client identification strategies
   - Rules and policies
   - Storage solutions (Redis-based)

3. **Technical Concepts:**
   - High availability considerations
   - Latency optimization
   - Race condition handling
   - HTTP 429 responses and headers

4. **Real-world Use Cases:**
   - E-commerce flash sale APIs
   - Social media spam prevention
   - Banking/payment gateway transaction limiting

## Working with This Repository

### Making Changes

**When editing documentation:**
- Maintain the existing markdown structure and formatting style
- Keep explanations clear, comprehensive, and educational
- Include code examples in appropriate languages (primarily Python pseudocode)
- Use diagrams and visual representations where helpful (ASCII art is used)
- Ensure technical accuracy when describing algorithms and system design concepts

**Style Guidelines:**
- Use emoji sparingly and only where already established (✅, ❌, 🪣, 💧, etc.)
- Maintain consistent heading hierarchy (# for main sections, ## for subsections)
- Keep code blocks properly formatted with language identifiers
- Use tables for comparing algorithm characteristics

### Validation

**Before committing changes:**
- Verify markdown syntax is correct
- Check that all links are valid (if any are added)
- Ensure code examples are syntactically correct
- Maintain consistency with existing documentation style

**Note:** This repository does NOT have:
- Python/Django code to test
- Dependencies to install
- Tests to run
- Build processes
- CI/CD pipelines

### Common Tasks

**Adding new algorithm documentation:**
1. Follow the existing structure (Concept → How It Works → Characteristics → Diagram → Use Case → Pseudocode)
2. Include a comparison table
3. Add visual ASCII diagram
4. Provide practical examples

**Updating existing content:**
1. Maintain the educational tone
2. Keep examples practical and relevant to production systems
3. Reference real-world implementations (Amazon, Uber, Stripe mentioned in README)

## Important Notes

- This repository currently contains **documentation only** (no implementation code)
- The README and documentation describe rate limiting concepts, algorithms, and how to implement them, but the actual Python/Django code is not present in this repository
- Focus changes on improving educational content, clarity, and technical accuracy
- No runtime testing, builds, or CI/CD validation is needed - only verify markdown syntax and correctness
