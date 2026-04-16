---
title: "Ollama Embeddings"
category: "Embeddings"
source: "Ollama Embeddings __ Spring AI Reference.pdf"
generated_by: "springai-kb-converter"
---

# Ollama Embeddings

Ollama can run embedding models locally, and Spring AI integrates with those models through `OllamaEmbeddingModel`.

Embeddings are numeric vectors. Smaller vector distance typically means stronger semantic similarity.

## Prerequisites

Before using embeddings, make sure you can access an Ollama instance.

Common setup choices include:

- local Ollama installation
- Testcontainers setup
- Kubernetes service binding to a remote Ollama host

Pull a model before use:

```bash
ollama pull <model-name>
```

Pull a GGUF model from Hugging Face:

```bash
ollama pull hf.co/<username>/<model-repository>
```

## Spring Boot Auto-Configuration

Add the Ollama model starter:

```xml
<dependency>
   <groupId>org.springframework.ai</groupId>
   <artifactId>spring-ai-starter-model-ollama</artifactId>
</dependency>
```

Use the `spring.ai.ollama` prefix for connection and model options.

### Core Properties

```yaml
spring:
  ai:
    ollama:
      base-url: http://localhost:11434
      embedding:
        options:
          model: mxbai-embed-large
```

Top-level embedding model enablement uses `spring.ai.model.embedding`:

- `ollama` to enable
- `none` (or any other value) to disable

## Runtime Options

Use `OllamaEmbeddingOptions` for per-request overrides such as model, truncate behavior, and low-level runtime tuning.

```java
EmbeddingResponse embeddingResponse = embeddingModel.call(
    new EmbeddingRequest(
        List.of("Hello World", "World is big and salvation is near"),
        OllamaEmbeddingOptions.builder()
            .model("nomic-embed-text")
            .truncate(false)
            .build()
    )
);
```

Use default options at startup and override only when needed for request-specific behavior.

## Auto-Pulling Models

Spring AI can auto-pull missing Ollama models at startup.

Supported strategies:

- `always`
- `when_missing`
- `never`

Example:

```yaml
spring:
  ai:
    ollama:
      init:
        pull-model-strategy: when_missing
        timeout: 60s
        max-retries: 1
```

Preload additional embedding models:

```yaml
spring:
  ai:
    ollama:
      init:
        pull-model-strategy: when_missing
        embedding:
          additional-models:
            - mxbai-embed-large
            - nomic-embed-text
```

Disable embedding-model initialization while still using init for other model types:

```yaml
spring:
  ai:
    ollama:
      init:
        pull-model-strategy: when_missing
        embedding:
          include: false
```

For production, pre-pull models ahead of deployment to reduce startup delays.

## Hugging Face GGUF Embedding Models

Ollama can run GGUF embedding models from Hugging Face.

Example configuration:

```properties
spring.ai.ollama.embedding.options.model=hf.co/mixedbread-ai/mxbai-embed-large-v1
spring.ai.ollama.init.pull-model-strategy=when_missing
```

For production environments, prefer explicit pre-download:

```bash
ollama pull hf.co/mixedbread-ai/mxbai-embed-large-v1
```

## Sample Controller

```java
@RestController
public class EmbeddingController {

    private final EmbeddingModel embeddingModel;

    public EmbeddingController(EmbeddingModel embeddingModel) {
        this.embeddingModel = embeddingModel;
    }

    @GetMapping("/ai/embedding")
    public Map<String, Object> embed(
            @RequestParam(value = "message", defaultValue = "Tell me a joke") String message) {
        EmbeddingResponse embeddingResponse = embeddingModel.embedForResponse(List.of(message));
        return Map.of("embedding", embeddingResponse);
    }
}
```

## Manual Configuration

If you are not using Spring Boot auto-configuration, configure `OllamaEmbeddingModel` manually.

Add the core Ollama module:

```xml
<dependency>
    <groupId>org.springframework.ai</groupId>
    <artifactId>spring-ai-ollama</artifactId>
</dependency>
```

Create the model instance:

```java
var ollamaApi = OllamaApi.builder().build();

var embeddingModel = new OllamaEmbeddingModel(
    ollamaApi,
    OllamaEmbeddingOptions.builder()
        .model("mxbai-embed-large")
        .build()
);

EmbeddingResponse embeddingResponse = embeddingModel.call(
    new EmbeddingRequest(
        List.of("Hello World", "World is big and salvation is near"),
        OllamaEmbeddingOptions.builder()
            .model("chroma/all-minilm-l6-v2-f32")
            .truncate(false)
            .build()
    )
);
```

## Notes

- Use `OllamaEmbeddingOptions` for embedding requests.
- Prefer model preloading in production.
- Keep runtime overrides minimal unless request-level tuning is required.
- Use task-appropriate embedding models for retrieval quality and latency trade-offs.
