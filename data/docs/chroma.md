---
title: "Chroma"
category: "Spring AI"
source: "Chroma __ Spring AI Reference.pdf"
generated_by: "springai-kb-converter"
---

# Chroma

This guide shows how to use Spring AI's `ChromaVectorStore` to store document embeddings and run similarity search with optional metadata filtering.

Chroma is an open-source embedding database for vectors, documents, and metadata.

## Prerequisites

1. Access to a ChromaDB instance.
   - Chroma Cloud: API key, tenant name, and database name.
   - Local ChromaDB: run a local container (see [Run Chroma Locally](#run-chroma-locally)).
2. A configured `EmbeddingModel` bean.
   - If your embedding model is hosted (for example, OpenAI), provide the required API key.

On startup, `ChromaVectorStore` can create missing tenant/database/collection resources when schema initialization is enabled.

## Auto-configuration

Spring AI provides Spring Boot auto-configuration for Chroma Vector Store.

Add the dependency to Maven:

```xml
<dependency>
    <groupId>org.springframework.ai</groupId>
    <artifactId>spring-ai-starter-vector-store-chroma</artifactId>
</dependency>
```

Or Gradle:

```groovy
dependencies {
    implementation 'org.springframework.ai:spring-ai-starter-vector-store-chroma'
}
```

Refer to Spring AI dependency management to import the BOM and to repository guidance for Maven Central and snapshots.

The vector store can initialize required schema elements, but this is opt-in. Set `spring.ai.vectorstore.chroma.initialize-schema=true` in properties, or call `.initializeSchema(true)` in builder-based setup.

This is a breaking change compared to older Spring AI versions where schema initialization happened by default.

You also need a configured `EmbeddingModel` bean:

```java
@Bean
public EmbeddingModel embeddingModel() {
    // Any EmbeddingModel implementation can be used.
    return new OpenAiEmbeddingModel(
        OpenAiApi.builder().apiKey(System.getenv("OPENAI_API_KEY")).build()
    );
}
```

Configure Chroma connection settings in `application.properties`:

```properties
## Chroma Vector Store connection properties
spring.ai.vectorstore.chroma.client.host=<your-chroma-host>
spring.ai.vectorstore.chroma.client.port=<your-chroma-port>
spring.ai.vectorstore.chroma.client.key-token=<your-access-token-if-configured>
spring.ai.vectorstore.chroma.client.username=<your-username-if-configured>
spring.ai.vectorstore.chroma.client.password=<your-password-if-configured>

## Chroma Vector Store tenant and database properties (required for Chroma Cloud)
spring.ai.vectorstore.chroma.tenant-name=<your-tenant-name>
spring.ai.vectorstore.chroma.database-name=<your-database-name>

## Chroma Vector Store collection properties
spring.ai.vectorstore.chroma.collection-name=<your-collection-name>
spring.ai.vectorstore.chroma.initialize-schema=<true|false>
```

If OpenAI auto-configuration is used:

```properties
spring.ai.openai.api.key=<openai-api-key>
```

Inject and use the vector store:

```java
@Autowired
VectorStore vectorStore;

List<Document> documents = List.of(
    new Document(
        "Spring AI rocks!! Spring AI rocks!! Spring AI rocks!! Spring AI rocks!! Spring AI rocks!!",
        Map.of("meta1", "meta1")
    ),
    new Document("The World is Big and Salvation Lurks Around the Corner"),
    new Document(
        "You walk forward facing the past and you turn back toward the future.",
        Map.of("meta2", "meta2")
    )
);

vectorStore.add(documents);

List<Document> results = vectorStore.similaritySearch(
    SearchRequest.builder().query("Spring").topK(5).build()
);
```

### Configuration Properties

| Property | Description | Default |
| --- | --- | --- |
| `spring.ai.vectorstore.chroma.client.host` | Server host | - |
| `spring.ai.vectorstore.chroma.client.port` | Server port | `8000` |
| `spring.ai.vectorstore.chroma.client.key-token` | Static API token (if configured) | - |
| `spring.ai.vectorstore.chroma.client.username` | Basic auth username (if configured) | - |
| `spring.ai.vectorstore.chroma.client.password` | Basic auth password (if configured) | - |
| `spring.ai.vectorstore.chroma.tenant-name` | Tenant name (required for Chroma Cloud) | `SpringAiTenant` |
| `spring.ai.vectorstore.chroma.database-name` | Database name (required for Chroma Cloud) | `SpringAiDatabase` |
| `spring.ai.vectorstore.chroma.collection-name` | Collection name | `SpringAiCollection` |
| `spring.ai.vectorstore.chroma.initialize-schema` | Create tenant/database/collection if missing | `false` |

Authentication helpers:

- Static token auth: `ChromaApi#withKeyToken(...)`
- Basic auth: `ChromaApi#withBasicAuth(<user>, <password>)`

### Chroma Cloud Configuration

For Chroma Cloud, use tenant and database names from your Chroma Cloud account:

```properties
## Chroma Cloud connection
spring.ai.vectorstore.chroma.client.host=api.trychroma.com
spring.ai.vectorstore.chroma.client.port=443
spring.ai.vectorstore.chroma.client.key-token=<your-chroma-cloud-api-key>

## Chroma Cloud tenant and database (required)
spring.ai.vectorstore.chroma.tenant-name=<your-tenant-id>
spring.ai.vectorstore.chroma.database-name=<your-database-name>

## Collection configuration
spring.ai.vectorstore.chroma.collection-name=my-collection
spring.ai.vectorstore.chroma.initialize-schema=true
```

Notes:

- Host should be `api.trychroma.com`.
- Port should be `443` (HTTPS).
- Provide your API key via `key-token`.
- Tenant and database names must match your cloud configuration.
- `initialize-schema=true` creates missing resources; it does not recreate existing tenant/database resources.

## Metadata Filtering

`ChromaVectorStore` supports generic, portable metadata filters.

Text expression example:

```java
vectorStore.similaritySearch(
    SearchRequest.builder()
        .query("The World")
        .topK(TOP_K)
        .similarityThreshold(SIMILARITY_THRESHOLD)
        .filterExpression("author in ['john', 'jill'] && article_type == 'blog'")
        .build()
);
```

Programmatic `Filter.Expression` DSL example:

```java
FilterExpressionBuilder b = new FilterExpressionBuilder();

vectorStore.similaritySearch(
    SearchRequest.builder()
        .query("The World")
        .topK(TOP_K)
        .similarityThreshold(SIMILARITY_THRESHOLD)
        .filterExpression(
            b.and(
                b.in("author", "john", "jill"),
                b.eq("article_type", "blog")
            ).build()
        )
        .build()
);
```

Portable filter expression:

```text
author in ['john', 'jill'] && article_type == 'blog'
```

Equivalent Chroma `where` format:

```json
{
  "$and": [
    { "author": { "$in": ["john", "jill"] } },
    { "article_type": { "$eq": "blog" } }
  ]
}
```

## Manual Configuration

If you prefer manual wiring, define `ChromaVectorStore` as a bean.

Dependencies:

Chroma Vector Store:

```xml
<dependency>
    <groupId>org.springframework.ai</groupId>
    <artifactId>spring-ai-chroma-store</artifactId>
</dependency>
```

Embedding model starter example (OpenAI):

```xml
<dependency>
    <groupId>org.springframework.ai</groupId>
    <artifactId>spring-ai-starter-model-openai</artifactId>
</dependency>
```

You can use any `EmbeddingModel` implementation.

### Sample Code

Create `RestClient.Builder` and `ChromaApi`:

```java
@Bean
public RestClient.Builder builder() {
    return RestClient.builder().requestFactory(new SimpleClientHttpRequestFactory());
}

@Bean
public ChromaApi chromaApi(RestClient.Builder restClientBuilder) {
    String chromaUrl = "http://localhost:8000";
    return new ChromaApi(chromaUrl, restClientBuilder);
}
```

Create the vector store bean:

```java
@Bean
public VectorStore chromaVectorStore(EmbeddingModel embeddingModel, ChromaApi chromaApi) {
    return ChromaVectorStore.builder(chromaApi, embeddingModel)
        .tenantName("your-tenant-name") // default: SpringAiTenant
        .databaseName("your-database-name") // default: SpringAiDatabase
        .collectionName("TestCollection")
        .initializeSchema(true)
        .build();
}
```

Create and index documents:

```java
List<Document> documents = List.of(
    new Document(
        "Spring AI rocks!! Spring AI rocks!! Spring AI rocks!! Spring AI rocks!! Spring AI rocks!!",
        Map.of("meta1", "meta1")
    ),
    new Document("The World is Big and Salvation Lurks Around the Corner"),
    new Document(
        "You walk forward facing the past and you turn back toward the future.",
        Map.of("meta2", "meta2")
    )
);

vectorStore.add(documents);
```

Similarity search:

```java
List<Document> results = vectorStore.similaritySearch("Spring");
```

If configured correctly, one of the results should include the document containing "Spring AI rocks!!".

### Run Chroma Locally

```bash
docker run -it --rm --name chroma -p 8000:8000 ghcr.io/chroma-core/chroma:1.0.0
```

This starts a local Chroma instance, typically available at `http://localhost:8000` (API path may vary by client configuration/version).
