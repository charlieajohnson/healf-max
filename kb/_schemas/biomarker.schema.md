---
id: biomarker
type: schema
title: Biomarker
status: active
retrieval_priority: 1
reviewed_at: '2026-07-01'
tags:
- schema
- biomarker
---
# Purpose

Defines the expected frontmatter shape for biomarker records.

# Required fields

`id`, `type`, `title`, `status`, `retrieval_priority`, `reviewed_at`.

# Notes

marker units, demo result, interpretation mode, action mode, escalation and routes. Health-related records must also include `safety_boundary` and `prohibited_claims`.
