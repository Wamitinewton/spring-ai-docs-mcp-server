---
title: "Spring AI API"
category: "Spring AI API"
source: "Spring AI API __ Spring AI Reference.pdf"
generated_by: "springai-kb-converter"
---

# Spring AI API

## Introduction

The Spring AI API covers a wide range of capabilities. Each major feature is detailed in its own dedicated section. At a high level, it includes:

### AI Model API

- Portable `Model API` across AI providers for `Chat`, `Text to Image`, `Audio Transcription`, `Text to Speech`, and `Embedding` models.
- Supports both `synchronous` and `stream` API options.
- Allows access to model-specific features when needed.
- Supports models from OpenAI, Microsoft, Amazon, Google, Amazon Bedrock, Hugging Face, and more.

### Vector Store API

- Portable `Vector Store API` across multiple providers.
- Includes a portable `SQL-like metadata filter API`.
- Supports 14 vector databases.

### Tool Calling API

Spring AI makes it easy for AI models to invoke your services through `@Tool`-annotated methods or POJO `java.util.Function` objects.

Check the Spring AI Tool Calling documentation.

### Auto Configuration

Spring Boot Auto Configuration and Starters for AI Models and Vector Stores.

### ETL Data Engineering

ETL framework for data engineering. This provides the foundation for loading data into a vector database and implementing the Retrieval Augmented Generation pattern, enabling your data to be incorporated into model responses.

## Feedback and Contributions

The project’s GitHub discussions are a great place to share feedback.
