---
title: "Chat Memory"
category: "Chat"
source: "Chat Memory __ Spring AI Reference.pdf"
generated_by: "springai-kb-converter"
---

# Chat Memory

Large language models (LLMs) are stateless. They do not retain prior interactions unless you provide relevant context on each request.

Spring AI addresses this with a `ChatMemory` abstraction that stores and retrieves conversation context.

- `ChatMemory`: decides what to keep and what to evict.
- `ChatMemoryRepository`: stores and retrieves messages.

Typical memory strategies include:

- Keep the last `N` messages.
- Keep messages for a time window.
- Keep messages within a token budget.

## Chat Memory vs Chat History

- Chat memory: the subset of messages used to maintain context for current reasoning.
- Chat history: the full record of all conversation events.

Use `ChatMemory` for context management. If you need full audit/history retention, use a dedicated persistence strategy (for example Spring Data-backed storage).

## Quick Start

Spring AI auto-configures a `ChatMemory` bean.

Default behavior:

- Repository: `InMemoryChatMemoryRepository`
- Memory policy: `MessageWindowChatMemory`

If another repository bean exists (for example JDBC, Cassandra, Neo4j), that one is used.

```java
@Autowired
ChatMemory chatMemory;
```

## Memory Types

### MessageWindowChatMemory

`MessageWindowChatMemory` maintains a bounded list of recent messages (default: `20`).
When the limit is exceeded, oldest non-system messages are evicted; system messages are preserved.

```java
ChatMemory memory = MessageWindowChatMemory.builder()
    .maxMessages(10)
    .build();
```

This is the default memory type used by Spring AI auto-configuration.

## Memory Storage Repositories

Spring AI provides multiple `ChatMemoryRepository` implementations. You can also implement your own.

### InMemoryChatMemoryRepository

Stores messages in-memory using a `ConcurrentHashMap`.

- Auto-configured when no other repository is present.
- Suitable for local development and single-instance runtime.

```java
@Autowired
ChatMemoryRepository chatMemoryRepository;
```

Manual creation:

```java
ChatMemoryRepository repository = new InMemoryChatMemoryRepository();
```

### JdbcChatMemoryRepository

Stores messages in relational databases via JDBC.

- Supports multiple SQL dialects.
- Returns messages oldest-to-newest.

Dependency:

```xml
<dependency>
    <groupId>org.springframework.ai</groupId>
    <artifactId>spring-ai-starter-model-chat-memory-repository-jdbc</artifactId>
</dependency>
```

Auto-configured usage:

```java
@Autowired
JdbcChatMemoryRepository chatMemoryRepository;

ChatMemory chatMemory = MessageWindowChatMemory.builder()
    .chatMemoryRepository(chatMemoryRepository)
    .maxMessages(10)
    .build();
```

Manual creation:

```java
ChatMemoryRepository chatMemoryRepository = JdbcChatMemoryRepository.builder()
    .jdbcTemplate(jdbcTemplate)
    .dialect(new PostgresChatMemoryRepositoryDialect())
    .build();

ChatMemory chatMemory = MessageWindowChatMemory.builder()
    .chatMemoryRepository(chatMemoryRepository)
    .maxMessages(10)
    .build();
```

Configuration properties:

| Property | Description | Default |
|---|---|---|
| `spring.ai.chat.memory.repository.jdbc.initialize-schema` | Schema initialization mode: `embedded`, `always`, `never` | `embedded` |
| `spring.ai.chat.memory.repository.jdbc.schema` | SQL script location for schema creation | `classpath:org/springframework/ai/chat/memory/repository/jdbc/schema-@@platform@@.sql` |
| `spring.ai.chat.memory.repository.jdbc.platform` | Platform name used in schema placeholder | Auto-detected |

Schema initialization example:

```properties
spring.ai.chat.memory.repository.jdbc.initialize-schema=embedded
spring.ai.chat.memory.repository.jdbc.initialize-schema=always
spring.ai.chat.memory.repository.jdbc.initialize-schema=never
```

Custom schema path:

```properties
spring.ai.chat.memory.repository.jdbc.schema=classpath:/custom/path/schema-mysql.sql
```

### CassandraChatMemoryRepository

Stores messages in Apache Cassandra.

- Suitable for high availability and horizontal scale.
- Supports TTL-based retention.
- Returns messages oldest-to-newest.

Dependency:

```xml
<dependency>
    <groupId>org.springframework.ai</groupId>
    <artifactId>spring-ai-starter-model-chat-memory-repository-cassandra</artifactId>
</dependency>
```

Auto-configured usage:

```java
@Autowired
CassandraChatMemoryRepository chatMemoryRepository;

ChatMemory chatMemory = MessageWindowChatMemory.builder()
    .chatMemoryRepository(chatMemoryRepository)
    .maxMessages(10)
    .build();
```

Manual creation:

```java
ChatMemoryRepository chatMemoryRepository = CassandraChatMemoryRepository
    .create(CassandraChatMemoryRepositoryConfig.builder().withCqlSession(cqlSession));

ChatMemory chatMemory = MessageWindowChatMemory.builder()
    .chatMemoryRepository(chatMemoryRepository)
    .maxMessages(10)
    .build();
```

Key properties:

| Property | Description | Default |
|---|---|---|
| `spring.cassandra.contact-points` | Initial Cassandra hosts | `127.0.0.1` |
| `spring.cassandra.port` | Cassandra native port | `9042` |
| `spring.cassandra.local-datacenter` | Cassandra datacenter | `datacenter1` |
| `spring.ai.chat.memory.repository.cassandra.time-to-live` | Message TTL | Not set |
| `spring.ai.chat.memory.repository.cassandra.keyspace` | Keyspace name | `springframework` |
| `spring.ai.chat.memory.repository.cassandra.table` | Table name | `ai_chat_memory` |
| `spring.ai.chat.memory.repository.cassandra.initialize-schema` | Create schema on startup | `true` |

### Neo4jChatMemoryRepository

Stores messages as graph nodes/relationships in Neo4j.

- Useful when graph traversal and relationships matter.
- Returns messages by ascending message index.

Dependency:

```xml
<dependency>
    <groupId>org.springframework.ai</groupId>
    <artifactId>spring-ai-starter-model-chat-memory-repository-neo4j</artifactId>
</dependency>
```

Auto-configured usage:

```java
@Autowired
Neo4jChatMemoryRepository chatMemoryRepository;

ChatMemory chatMemory = MessageWindowChatMemory.builder()
    .chatMemoryRepository(chatMemoryRepository)
    .maxMessages(10)
    .build();
```

Manual creation:

```java
ChatMemoryRepository chatMemoryRepository = Neo4jChatMemoryRepository.builder()
    .driver(driver)
    .build();
```

Key label properties:

| Property | Description | Default |
|---|---|---|
| `spring.ai.chat.memory.repository.neo4j.sessionLabel` | Session node label | `Session` |
| `spring.ai.chat.memory.repository.neo4j.messageLabel` | Message node label | `Message` |
| `spring.ai.chat.memory.repository.neo4j.toolCallLabel` | Tool call node label | `ToolCall` |
| `spring.ai.chat.memory.repository.neo4j.metadataLabel` | Metadata node label | `Metadata` |
| `spring.ai.chat.memory.repository.neo4j.toolResponseLabel` | Tool response node label | `ToolResponse` |
| `spring.ai.chat.memory.repository.neo4j.mediaLabel` | Media node label | `Media` |

The repository ensures required indexes are present for conversation and message lookup.

### CosmosDBChatMemoryRepository

Stores messages in Azure Cosmos DB (NoSQL API).

- Uses conversation ID as partition key.
- Suitable for globally distributed, scalable persistence.
- Returns messages oldest-to-newest.

Dependency:

```xml
<dependency>
    <groupId>org.springframework.ai</groupId>
    <artifactId>spring-ai-starter-model-chat-memory-repository-cosmos-db</artifactId>
</dependency>
```

Auto-configured usage:

```java
@Autowired
CosmosDBChatMemoryRepository chatMemoryRepository;

ChatMemory chatMemory = MessageWindowChatMemory.builder()
    .chatMemoryRepository(chatMemoryRepository)
    .maxMessages(10)
    .build();
```

Manual creation:

```java
ChatMemoryRepository chatMemoryRepository = CosmosDBChatMemoryRepository
    .create(CosmosDBChatMemoryRepositoryConfig.builder()
        .withCosmosClient(cosmosAsyncClient)
        .withDatabaseName("chat-memory-db")
        .withContainerName("conversations")
        .build());
```

Key properties:

| Property | Description | Default |
|---|---|---|
| `spring.ai.chat.memory.repository.cosmosdb.endpoint` | Cosmos DB endpoint URI | Required |
| `spring.ai.chat.memory.repository.cosmosdb.key` | Account key (optional with Azure Identity) | Not set |
| `spring.ai.chat.memory.repository.cosmosdb.connection-mode` | `direct` or `gateway` | `gateway` |
| `spring.ai.chat.memory.repository.cosmosdb.database-name` | Database name | `SpringAIChatMemory` |
| `spring.ai.chat.memory.repository.cosmosdb.container-name` | Container name | `ChatMemory` |
| `spring.ai.chat.memory.repository.cosmosdb.partition-key-path` | Partition key path | `/conversationId` |

Authentication options:

- Key-based authentication via `...cosmosdb.key`
- Azure Identity (`DefaultAzureCredential`) when no key is provided

### MongoChatMemoryRepository

Stores messages in MongoDB.

- Flexible document persistence.
- Returns messages oldest-to-newest.

Dependency:

```xml
<dependency>
    <groupId>org.springframework.ai</groupId>
    <artifactId>spring-ai-starter-model-chat-memory-repository-mongodb</artifactId>
</dependency>
```

Auto-configured usage:

```java
@Autowired
MongoChatMemoryRepository chatMemoryRepository;

ChatMemory chatMemory = MessageWindowChatMemory.builder()
    .chatMemoryRepository(chatMemoryRepository)
    .maxMessages(10)
    .build();
```

Manual creation:

```java
ChatMemoryRepository chatMemoryRepository = MongoChatMemoryRepository.builder()
    .mongoTemplate(mongoTemplate)
    .build();
```

Key properties:

| Property | Description | Default |
|---|---|---|
| `spring.ai.chat.memory.repository.mongo.create-indices` | Auto-create/recreate indexes | `false` |
| `spring.ai.chat.memory.repository.mongo.ttl` | TTL (seconds), `0` means no expiry | `0` |

## Memory in ChatClient

When using `ChatClient`, memory is typically managed through advisors.

Available advisors:

- `MessageChatMemoryAdvisor`: injects prior conversation as message objects.
- `PromptChatMemoryAdvisor`: appends memory as text to the system prompt.
- `VectorStoreChatMemoryAdvisor`: retrieves long-term memory from a `VectorStore` and appends it to the system prompt.

Note: intermediate tool-call messages are currently not persisted by default.

Example with `MessageWindowChatMemory`:

```java
ChatMemory chatMemory = MessageWindowChatMemory.builder().build();

ChatClient chatClient = ChatClient.builder(chatModel)
    .defaultAdvisors(MessageChatMemoryAdvisor.builder(chatMemory).build())
    .build();

String conversationId = "007";

String content = chatClient.prompt()
    .user("Do I have license to code?")
    .advisors(a -> a.param(ChatMemory.CONVERSATION_ID, conversationId))
    .call()
    .content();
```

### Custom Prompt Templates for Memory Advisors

`PromptChatMemoryAdvisor` and `VectorStoreChatMemoryAdvisor` support custom `PromptTemplate` objects.

Required placeholders:

- For `PromptChatMemoryAdvisor`: `instructions`, `memory`
- For `VectorStoreChatMemoryAdvisor`: `instructions`, `long_term_memory`

This template customization is advisor-level behavior and is separate from `ChatClient.templateRenderer(...)`.

## Memory in ChatModel

If you use `ChatModel` directly, memory management is explicit:

```java
ChatMemory chatMemory = MessageWindowChatMemory.builder().build();
String conversationId = "007";

UserMessage userMessage1 = new UserMessage("My name is James Bond");
chatMemory.add(conversationId, userMessage1);
ChatResponse response1 = chatModel.call(new Prompt(chatMemory.get(conversationId)));
chatMemory.add(conversationId, response1.getResult().getOutput());

UserMessage userMessage2 = new UserMessage("What is my name?");
chatMemory.add(conversationId, userMessage2);
ChatResponse response2 = chatModel.call(new Prompt(chatMemory.get(conversationId)));
chatMemory.add(conversationId, response2.getResult().getOutput());
```

The second response should include the remembered context (for example, "James Bond").
