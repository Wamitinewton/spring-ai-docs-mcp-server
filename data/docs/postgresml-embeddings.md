---
title: "PostgresML Embeddings"
category: "Embeddings"
source: "PostgresML Embeddings __ Spring AI Reference.pdf"
generated_by: "springai-kb-converter"
---

# PostgresML Embeddings

Spring AI supports text embeddings through PostgresML.

Embeddings map text to vectors, which can be used for semantic similarity, retrieval, ranking, and as features for downstream ML tasks.

## Overview

`PostgresMlEmbeddingModel` uses PostgresML embedding functions to generate vectors directly from PostgreSQL.

You can use a wide range of Hugging Face transformer models with PostgresML, depending on your runtime and hardware constraints.

## Auto-Configuration

Add the PostgresML embedding starter dependency.

```xml
<dependency>
    <groupId>org.springframework.ai</groupId>
    <artifactId>spring-ai-starter-model-postgresml-embedding</artifactId>
</dependency>
```

For Gradle:

```groovy
dependencies {
    implementation 'org.springframework.ai:spring-ai-starter-model-postgresml-embedding'
}
```

## Configuration Properties

Use `spring.ai.postgresml.embedding` for PostgresML embedding configuration.

### Top-Level Model Enablement

```properties
spring.ai.model.embedding=postgresml
```

Disable with:

```properties
spring.ai.model.embedding=none
```

### Typical Embedding Options

```properties
spring.ai.postgresml.embedding.create-extension=false
spring.ai.postgresml.embedding.options.transformer=distilbert-base-uncased
spring.ai.postgresml.embedding.options.vectorType=PG_ARRAY
spring.ai.postgresml.embedding.options.metadataMode=EMBED
spring.ai.postgresml.embedding.options.kwargs.device=cpu
```

Common options include:

- `transformer`: Hugging Face model name
- `vectorType`: `PG_ARRAY` or `PG_VECTOR`
- `metadataMode`: document metadata aggregation mode
- `kwargs`: extra model/runtime arguments

## Runtime Options

Use `PostgresMlEmbeddingOptions` to override defaults for a specific embedding request.

```java
EmbeddingResponse embeddingResponse = embeddingModel.call(
    new EmbeddingRequest(
        List.of("Hello World", "World is big and salvation is near"),
        PostgresMlEmbeddingOptions.builder()
            .transformer("intfloat/e5-small")
            .vectorType(VectorType.PG_ARRAY)
            .kwargs(Map.of("device", "gpu"))
            .build()
    )
);
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

If you are not using Spring Boot auto-configuration, add the core PostgresML module.

```xml
<dependency>
    <groupId>org.springframework.ai</groupId>
    <artifactId>spring-ai-postgresml</artifactId>
</dependency>
```

For Gradle:

```groovy
dependencies {
    implementation 'org.springframework.ai:spring-ai-postgresml'
}
```

Create the model manually:

```java
var jdbcTemplate = new JdbcTemplate(dataSource);

PostgresMlEmbeddingModel embeddingModel = new PostgresMlEmbeddingModel(
    jdbcTemplate,
    PostgresMlEmbeddingOptions.builder()
        .transformer("distilbert-base-uncased")
        .vectorType(VectorType.PG_VECTOR)
        .kwargs(Map.of("device", "cpu"))
        .metadataMode(MetadataMode.EMBED)
        .build()
);

embeddingModel.afterPropertiesSet();

EmbeddingResponse embeddingResponse = embeddingModel.embedForResponse(
    List.of("Hello World", "World is big and salvation is near")
);
```

If you register the model as a Spring bean, lifecycle callbacks are handled automatically.

```java
@Bean
public EmbeddingModel embeddingModel(JdbcTemplate jdbcTemplate) {
    return new PostgresMlEmbeddingModel(
        jdbcTemplate,
        PostgresMlEmbeddingOptions.builder()
            .transformer("distilbert-base-uncased")
            .vectorType(VectorType.PG_VECTOR)
            .metadataMode(MetadataMode.EMBED)
            .build()
    );
}
```

## Notes

- Use `PG_VECTOR` when you want tighter integration with pgvector-based search.
- Use `kwargs` to tune device/runtime behavior.
- Keep request-level overrides focused on scenario-specific needs.
- Select transformer models based on embedding quality, latency, and hardware limits.
