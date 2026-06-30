# MCP Server Evaluation Guide

## Overview

This document provides guidance on creating comprehensive evaluations for MCP servers. Evaluations test whether LLMs can effectively use your MCP server to answer realistic, complex questions using only the tools provided.

---

## Quick Reference

### Evaluation Requirements
- Create 10 human-readable questions
- Questions must be READ-ONLY, INDEPENDENT, NON-DESTRUCTIVE
- Each question requires multiple tool calls
- Answers must be single, verifiable values
- Answers must be STABLE (won't change over time)

### Output Format
```xml
<evaluation>
   <qa_pair>
      <question>Your question here</question>
      <answer>Single verifiable answer</answer>
   </qa_pair>
</evaluation>
```

---

## Question Guidelines

### Core Requirements
1. **Questions MUST be independent** - No question should depend on another
2. **Questions MUST require ONLY NON-DESTRUCTIVE tool use**
3. **Questions must be REALISTIC, CLEAR, CONCISE, and COMPLEX**
4. **Questions must require deep exploration** - Multi-hop questions with sequential tool calls
5. **Questions may require extensive paging** through multiple pages
6. **Questions must not be solvable with straightforward keyword search** - Use synonyms, paraphrases

### Stability
- Questions must be designed so the answer DOES NOT CHANGE
- Do not ask questions that rely on "current state" which is dynamic
- Use historical data and closed concepts

### Answer Guidelines
- Answers must be VERIFIABLE via direct string comparison
- Prefer HUMAN-READABLE formats (names, dates, yes/no, etc.)
- Must be CLEAR and UNAMBIGUOUS
- Must be DIVERSE across different data types

---

## Evaluation Process

### Step 1: Documentation Inspection
Read the documentation of the target API to understand available endpoints and functionality.

### Step 2: Tool Inspection
List the tools available in the MCP server and understand input/output schemas.

### Step 3: Developing Understanding
Repeat steps 1 & 2 until you have a good understanding of the API and tools.

### Step 4: Read-Only Content Inspection
Use the MCP server tools to inspect content using READ-ONLY operations only.

### Step 5: Task Generation
Create 10 human-readable questions following all guidelines above.

---

## Running Evaluations

### Setup
```bash
pip install anthropic mcp
export ANTHROPIC_API_KEY=your_api_key_here
```

### Command
```bash
python scripts/evaluation.py \
  -t stdio \
  -c python \
  -a my_mcp_server.py \
  evaluation.xml
```

### Output
The evaluation script generates a detailed report including:
- Summary Statistics (accuracy, avg duration, avg tool calls)
- Per-Task Results (prompt, expected/actual response, correct/incorrect)
