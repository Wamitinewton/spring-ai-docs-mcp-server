---
title: "Retrieval Augmented Generation"
category: "Spring AI"
source: "Retrieval Augmented Generation __ Spring AI Reference.pdf"
generated_by: "springai-kb-converter"
---

# Retrieval Augmented Generation

Retrieval Augmented Generation (RAG) is a technique used to overcome limitations of large language models that struggle with long-form content, factual accuracy, and context awareness.

Spring AI supports RAG by providing a modular architecture that lets you build custom RAG flows or use out-of-the-box flows with the `Advisor` API.

Learn more about Retrieval Augmented Generation in the concepts section.

## Advisors

Spring AI provides out-of-the-box support for common RAG flows using the `Advisor` API.

To use `QuestionAnswerAdvisor` or `VectorStoreChatMemoryAdvisor`, add the `spring-ai-advisors-vector-store` dependency to your project:

```xml
<dependency>
   <groupId>org.springframework.ai</groupId>
   <artifactId>spring-ai-advisors-vector-store</artifactId>
</dependency>
```

### QuestionAnswerAdvisor

A vector database stores data that the AI model is unaware of. When a user question is sent to the AI model, `QuestionAnswerAdvisor` queries the vector database for related documents.

The response from the vector database is appended to the user text to provide context for the AI model to generate a response.

Assuming data is already loaded into a `VectorStore`, you can perform RAG by providing a `QuestionAnswerAdvisor` to `ChatClient`.

```java
ChatResponse response = ChatClient.builder(chatModel)
        .build().prompt()
        .advisors(QuestionAnswerAdvisor.builder(vectorStore).build())
        .user(userText)
        .call()
        .chatResponse();
```

In this example, `QuestionAnswerAdvisor` performs a similarity search over all documents in the vector database. To restrict the types of documents searched, `SearchRequest` accepts a SQL-like filter expression that is portable across all `VectorStore` implementations.

This filter expression can be configured when creating `QuestionAnswerAdvisor` (always applied), or provided at runtime per request.

Here is how to create a `QuestionAnswerAdvisor` with a threshold of `0.8` and top `6` results:

```java
var qaAdvisor = QuestionAnswerAdvisor.builder(vectorStore)
        .searchRequest(SearchRequest.builder().similarityThreshold(0.8d).topK(6).build())
        .build();
```

#### Dynamic Filter Expressions

Update the `SearchRequest` filter expression at runtime using the `FILTER_EXPRESSION` advisor context parameter:

```java
ChatClient chatClient = ChatClient.builder(chatModel)
    .defaultAdvisors(QuestionAnswerAdvisor.builder(vectorStore)
        .searchRequest(SearchRequest.builder().build())
        .build())
    .build();
```

```java
// Update filter expression at runtime
String content = this.chatClient.prompt()
    .user("Please answer my question XYZ")
    .advisors(a -> a.param(QuestionAnswerAdvisor.FILTER_EXPRESSION, "type == 'Spring'"))
    .call()
    .content();
```

The `FILTER_EXPRESSION` parameter allows dynamic filtering of search results.

#### Custom Template

`QuestionAnswerAdvisor` uses a default template to augment the user question with retrieved documents. You can customize this behavior by providing your own `PromptTemplate` via `.promptTemplate()`.

The `PromptTemplate` customizes how the advisor merges retrieved context with the user query. This is distinct from configuring a `TemplateRenderer` on `ChatClient` itself (using `.templateRenderer()`), which affects rendering of the initial user/system prompt before the advisor runs.

The custom `PromptTemplate` can use any `TemplateRenderer` implementation (by default, it uses `StPromptTemplate` based on the StringTemplate engine). The template must contain these placeholders:

- `query` to receive the user question.
- `question_answer_context` to receive the retrieved context.

```java
PromptTemplate customPromptTemplate = PromptTemplate.builder()
    .renderer(StTemplateRenderer.builder().startDelimiterToken('<').endDelimiterToken('>').build())
    .template("""
            <query>
            Context information is below.

---------------------
<question_answer_context>
---------------------

Given the context information and no prior knowledge, answer the query.

Follow these rules:
1. If the answer is not in the context, just say that you don't know.
2. Avoid statements like "Based on the context..." or "The provided information...".
            """)
    .build();

String question = "Where does the adventure of Anacletus and Birba take place?";

QuestionAnswerAdvisor qaAdvisor = QuestionAnswerAdvisor.builder(vectorStore)
    .promptTemplate(customPromptTemplate)
    .build();

String response = ChatClient.builder(chatModel).build()
    .prompt(question)
    .advisors(qaAdvisor)
    .call()
    .content();
```

The `QuestionAnswerAdvisor.Builder.userTextAdvise()` method is deprecated in favor of `.promptTemplate()`.

### RetrievalAugmentationAdvisor

Spring AI includes a library of RAG modules that you can use to build your own flows. `RetrievalAugmentationAdvisor` is an `Advisor` that provides an out-of-the-box implementation for common RAG flows based on modular architecture.

To use `RetrievalAugmentationAdvisor`, add the `spring-ai-rag` dependency to your project:

```xml
<dependency>
   <groupId>org.springframework.ai</groupId>
   <artifactId>spring-ai-rag</artifactId>
</dependency>
```

#### Sequential RAG Flows

```java
Advisor retrievalAugmentationAdvisor = RetrievalAugmentationAdvisor.builder()
        .documentRetriever(VectorStoreDocumentRetriever.builder()
                .similarityThreshold(0.50)
                .vectorStore(vectorStore)
                .build())
        .build();

String answer = chatClient.prompt()
        .advisors(retrievalAugmentationAdvisor)
        .user(question)
        .call()
        .content();
```

By default, `RetrievalAugmentationAdvisor` does not allow retrieved context to be empty. When context is empty, it instructs the model not to answer. You can allow empty context as follows:

```java
Advisor retrievalAugmentationAdvisor = RetrievalAugmentationAdvisor.builder()
        .documentRetriever(VectorStoreDocumentRetriever.builder()
                .similarityThreshold(0.50)
                .vectorStore(vectorStore)
                .build())
        .queryAugmenter(ContextualQueryAugmenter.builder()
                .allowEmptyContext(true)
                .build())
        .build();

String answer = chatClient.prompt()
        .advisors(retrievalAugmentationAdvisor)
        .user(question)
        .call()
        .content();
```

`VectorStoreDocumentRetriever` accepts a `FilterExpression` to filter search results based on metadata. You can provide one when instantiating `VectorStoreDocumentRetriever`, or at runtime per request using the `FILTER_EXPRESSION` advisor context parameter.

#### Runtime Filter Expressions

```java
Advisor retrievalAugmentationAdvisor = RetrievalAugmentationAdvisor.builder()
        .documentRetriever(VectorStoreDocumentRetriever.builder()
                .similarityThreshold(0.50)
                .vectorStore(vectorStore)
                .build())
        .build();

String answer = chatClient.prompt()
        .advisors(retrievalAugmentationAdvisor)
        .advisors(a -> a.param(VectorStoreDocumentRetriever.FILTER_EXPRESSION, "type == 'Spring'"))
        .user(question)
        .call()
        .content();
```

See VectorStoreDocumentRetriever for more information.

#### Query Rewriting

```java
Advisor retrievalAugmentationAdvisor = RetrievalAugmentationAdvisor.builder()
        .queryTransformers(RewriteQueryTransformer.builder()
                .chatClientBuilder(chatClientBuilder.build().mutate())
                .build())
        .documentRetriever(VectorStoreDocumentRetriever.builder()
                .similarityThreshold(0.50)
                .vectorStore(vectorStore)
                .build())
        .build();

String answer = chatClient.prompt()
        .advisors(retrievalAugmentationAdvisor)
        .user(question)
        .call()
        .content();
```

You can also use the `DocumentPostProcessor` API to post-process retrieved documents before passing them to the model. For example, you can perform re-ranking, remove irrelevant or redundant documents, or compress content to reduce noise and redundancy.

## Modules

Spring AI implements a modular RAG architecture inspired by the paper "Modular RAG: Transforming RAG Systems into LEGO-like Reconfigurable Frameworks".

### Pre-Retrieval

Pre-Retrieval modules are responsible for processing the user query to achieve the best possible retrieval results.

#### Query Transformation

A query transformer makes the input query more effective for retrieval tasks, addressing challenges such as poorly formed queries, ambiguous terms, complex vocabulary, or unsupported languages.

When using a `QueryTransformer`, it is recommended to configure `ChatClient.Builder` with a low temperature (for example, `0.0`) to improve determinism and retrieval quality. The default temperature for many chat models is often too high for optimal query transformation.

A `CompressionQueryTransformer` uses a large language model to compress conversation history and a follow-up query into a standalone query.

This transformer is useful when the conversation history is long and the follow-up query is related to the conversation context.

```java
Query query = Query.builder()
        .text("And what is its second largest city?")
        .history(new UserMessage("What is the capital of Denmark?"),
                new AssistantMessage("Copenhagen is the capital of Denmark."))
        .build();

QueryTransformer queryTransformer = CompressionQueryTransformer.builder()
        .chatClientBuilder(chatClientBuilder)
        .build();

Query transformedQuery = queryTransformer.transform(query);
```

The prompt used by this component can be customized via the `promptTemplate()` method available in the builder.

A `RewriteQueryTransformer` uses a large language model to rewrite a user query for better retrieval results from a target system such as a vector store or web search engine.

This transformer is useful when the user query is verbose, ambiguous, or contains irrelevant information.

```java
Query query = new Query("I'm studying machine learning. What is an LLM?");

QueryTransformer queryTransformer = RewriteQueryTransformer.builder()
        .chatClientBuilder(chatClientBuilder)
        .build();

Query transformedQuery = queryTransformer.transform(query);
```

The prompt used by this component can be customized via the `promptTemplate()` method available in the builder.

A `TranslationQueryTransformer` uses a large language model to translate a query to a target language supported by the embedding model used for document embeddings. If the query is already in the target language, it is returned unchanged. If the language is unknown, it is also returned unchanged.

This transformer is useful when the embedding model is trained on a specific language and the user query is in a different language.

```java
Query query = new Query("Hvad er Danmarks hovedstad?");

QueryTransformer queryTransformer = TranslationQueryTransformer.builder()
        .chatClientBuilder(chatClientBuilder)
        .targetLanguage("english")
        .build();

Query transformedQuery = queryTransformer.transform(query);
```

The prompt used by this component can be customized via the `promptTemplate()` method available in the builder.

#### Query Expansion

A query expander expands an input query into a list of queries by providing alternative formulations or breaking down complex problems into simpler sub-queries.

A `MultiQueryExpander` uses a large language model to expand a query into multiple semantically diverse variations to capture different perspectives.

```java
MultiQueryExpander queryExpander = MultiQueryExpander.builder()
    .chatClientBuilder(chatClientBuilder)
    .numberOfQueries(3)
    .build();
List<Query> queries = queryExpander.expand(new Query("How to run a Spring Boot app?"));
```

By default, `MultiQueryExpander` includes the original query in the expanded query list. You can disable this via `includeOriginal` in the builder.

```java
MultiQueryExpander queryExpander = MultiQueryExpander.builder()
    .chatClientBuilder(chatClientBuilder)
    .includeOriginal(false)
    .build();
```

The prompt used by this component can be customized via the `promptTemplate()` method available in the builder.

### Retrieval

Retrieval modules are responsible for querying data systems like vector store and retrieving the most relevant documents.

#### Document Search

This component retrieves `Document` objects from an underlying data source such as a search engine, vector store, database, or knowledge graph.

A `VectorStoreDocumentRetriever` retrieves documents from a vector store that are semantically similar to the input query. It supports filtering by metadata, similarity threshold, and top-k results.

```java
DocumentRetriever retriever = VectorStoreDocumentRetriever.builder()
    .vectorStore(vectorStore)
    .similarityThreshold(0.73)
    .topK(5)
    .filterExpression(new FilterExpressionBuilder()
        .eq("genre", "fairytale")
        .build())
    .build();
List<Document> documents = retriever.retrieve(new Query("What is the main character of the story?"));
```

The filter expression can be static or dynamic. For dynamic filter expressions, you can pass a `Supplier`.

```java
DocumentRetriever retriever = VectorStoreDocumentRetriever.builder()
    .vectorStore(vectorStore)
    .filterExpression(() -> new FilterExpressionBuilder()
        .eq("tenant", TenantContextHolder.getTenantIdentifier())
        .build())
    .build();
List<Document> documents = retriever.retrieve(new Query("What are the KPIs for the next semester?"));
```

You can also provide a request-specific filter expression via the `Query` API using the `FILTER_EXPRESSION` parameter. If both request-specific and retriever-specific filter expressions are provided, the request-specific expression takes precedence.

```java
Query query = Query.builder()
    .text("Who is Anacletus?")
    .context(Map.of(VectorStoreDocumentRetriever.FILTER_EXPRESSION, "location == 'Whispering Woods'"))
    .build();
List<Document> retrievedDocuments = documentRetriever.retrieve(query);
```

#### Document Join

A document joiner combines documents retrieved from multiple queries and data sources into a single collection. As part of the joining process, it can also handle duplicate documents and reciprocal ranking strategies.

A `ConcatenationDocumentJoiner` combines retrieved documents by concatenating them. In case of duplicates, the first occurrence is kept, and each document score is preserved.

```java
Map<Query, List<List<Document>>> documentsForQuery = ...
DocumentJoiner documentJoiner = new ConcatenationDocumentJoiner();
List<Document> documents = documentJoiner.join(documentsForQuery);
```

### Post-Retrieval

Post-Retrieval modules are responsible for processing the retrieved documents to achieve the best possible generation results.

#### Document Post-Processing

A post-processor handles retrieved documents based on a query, addressing challenges such as lost-in-the-middle effects, context-length restrictions, and reducing noise and redundancy.

For example, it can rank documents by relevance, remove irrelevant or redundant documents, or compress content.

### Generation

Generation modules are responsible for generating the final response based on the user query and retrieved documents.

#### Query Augmentation

A query augmenter enriches an input query with additional data so the model has the context needed to answer.

`ContextualQueryAugmenter` augments the user query with contextual data from provided documents.

```java
QueryAugmenter queryAugmenter = ContextualQueryAugmenter.builder().build();
```

By default, `ContextualQueryAugmenter` does not allow empty retrieved context. In that case, it instructs the model not to answer.

You can enable `allowEmptyContext` to allow a response even when retrieved context is empty.

```java
QueryAugmenter queryAugmenter = ContextualQueryAugmenter.builder()
        .allowEmptyContext(true)
        .build();
```

The prompts used by this component can be customized via `promptTemplate()` and `emptyContextPromptTemplate()` in the builder.
