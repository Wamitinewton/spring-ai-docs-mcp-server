---
title: "Advisors API"
category: "Advisors"
source: "Advisors API __ Spring AI Reference.pdf"
generated_by: "springai-kb-converter"
---

# Advisors API

The Spring AI Advisors API provides a flexible and powerful way to intercept, modify, and enhance AI-driven interactions in your Spring applications. By leveraging the Advisors API, developers can create more sophisticated, reusable, and maintainable AI components.

Key benefits include encapsulating recurring Generative AI patterns, transforming data sent to and from Large Language Models (LLMs), and providing portability across various models and use cases.

You can configure existing advisors using the ChatClient API as shown in the following example:

```java
// Initialize your chat memory store and vector store
ChatMemory chatMemory = ...;
VectorStore vectorStore = ...;

var chatClient = ChatClient.builder(chatModel)
    .defaultAdvisors(
        MessageChatMemoryAdvisor.builder(chatMemory).build(), // chat-memory advisor
        QuestionAnswerAdvisor.builder(vectorStore).build()    // RAG advisor
    )
    .build();

var conversationId = "678";

String response = this.chatClient.prompt()
    // Set advisor parameters at runtime
    .advisors(advisor -> advisor.param(ChatMemory.CONVERSATION_ID, conversationId))
    .user(userText)
    .call()
    .content();
```

It is recommended to register the advisors at build time using the builder’s `defaultAdvisors()` method.

Advisors also participate in the Observability stack, so you can view metrics and traces related to their execution.

---

## Core Components

The API consists of:

- `CallAdvisor` and `CallAdvisorChain` for non-streaming scenarios
- `StreamAdvisor` and `StreamAdvisorChain` for streaming scenarios
- `ChatClientRequest` to represent the unsealed Prompt request
- `ChatClientResponse` for the Chat Completion response

Both request and response hold an `advise-context` to share state across the advisor chain.

The key advisor methods are `adviseCall()` and `adviseStream()`, which typically:
- Examine and customize the Prompt data
- Invoke the next entity in the advisor chain (or block the request and fill out the response)
- Examine and modify the chat completion response
- Throw exceptions to indicate processing errors

The `getOrder()` method determines advisor order in the chain, while `getName()` provides a unique advisor name.

---

## Advisor Chain Flow

The Advisor Chain, created by the Spring AI framework, allows sequential invocation of multiple advisors ordered by their `getOrder()` values (lower values are executed first). The last advisor, added automatically, sends the request to the LLM.

**Flow:**
1. The Spring AI framework creates a `ChatClientRequest` from the user’s `Prompt` along with an empty advisor `context` object.
2. Each advisor in the chain processes the request, potentially modifying it. Advisors can block the request (and must fill out the response) or pass it along.
3. The final advisor (provided by the framework) sends the request to the Chat Model.
4. The Chat Model’s response is passed back through the advisor chain and converted into a `ChatClientResponse`, including the shared advisor `context`.
5. Each advisor can process or modify the response.
6. The final `ChatClientResponse` is returned to the client by extracting the `ChatCompletion`.

---

### Advisor Order

The execution order of advisors in the chain is determined by the `getOrder()` method:

- Advisors with lower order values are executed first.
- The advisor chain operates as a stack:
    - The first advisor in the chain is the first to process the request.
    - It is also the last to process the response.
- To control execution order:
    - Set the order close to `Ordered.HIGHEST_PRECEDENCE` to execute first (for request), last (for response).
    - Set the order close to `Ordered.LOWEST_PRECEDENCE` to execute last (for request), first (for response).
- Higher values are interpreted as lower priority.
- If multiple advisors have the same order value, their execution order is not guaranteed.

This stack-like nature means:
- An advisor with the highest precedence (lowest order value) is added to the top of the stack.
- It will be the first to process the request as the stack unwinds, and the last to process the response as the stack rewinds.

```java
public interface Ordered {
    int HIGHEST_PRECEDENCE = Integer.MIN_VALUE;
    int LOWEST_PRECEDENCE = Integer.MAX_VALUE;
    int getOrder();
}
```

For use cases that need to be first in the chain on both the input and output sides, use the advisor context to share state between them.

---

## API Overview

The main Advisor interfaces are located in the package `org.springframework.ai.chat.client.advisor.api`. Key interfaces:

```java
public interface Advisor extends Ordered {
    String getName();
}

public interface CallAdvisor extends Advisor {
    ChatClientResponse adviseCall(
        ChatClientRequest chatClientRequest, CallAdvisorChain callAdvisorChain);
}

public interface StreamAdvisor extends Advisor {
    Flux<ChatClientResponse> adviseStream(
        ChatClientRequest chatClientRequest, StreamAdvisorChain streamAdvisorChain);
}

public interface CallAdvisorChain extends AdvisorChain {
    ChatClientResponse nextCall(ChatClientRequest chatClientRequest);
    List<CallAdvisor> getCallAdvisors();
}

public interface StreamAdvisorChain extends AdvisorChain {
    Flux<ChatClientResponse> nextStream(ChatClientRequest chatClientRequest);
    List<StreamAdvisor> getStreamAdvisors();
}
```

---

## Implementing an Advisor

To create an advisor, implement either `CallAdvisor` or `StreamAdvisor` (or both). The key method to implement is `adviseCall()` for non-streaming or `adviseStream()` for streaming advisors.

### Example: Logging Advisor

This advisor logs the `ChatClientRequest` before and the `ChatClientResponse` after the call to the next advisor in the chain. It supports both non-streaming and streaming scenarios.

```java
public class SimpleLoggerAdvisor implements CallAdvisor, StreamAdvisor {
    private static final Logger logger = LoggerFactory.getLogger(SimpleLoggerAdvisor.class);

    @Override
    public String getName() {
        return this.getClass().getSimpleName();
    }

    @Override
    public int getOrder() {
        return 0;
    }

    @Override
    public ChatClientResponse adviseCall(ChatClientRequest chatClientRequest, CallAdvisorChain callAdvisorChain) {
        logRequest(chatClientRequest);
        ChatClientResponse chatClientResponse = callAdvisorChain.nextCall(chatClientRequest);
        logResponse(chatClientResponse);
        return chatClientResponse;
    }

    @Override
    public Flux<ChatClientResponse> adviseStream(ChatClientRequest chatClientRequest, StreamAdvisorChain streamAdvisorChain) {
        logRequest(chatClientRequest);
        Flux<ChatClientResponse> chatClientResponses = streamAdvisorChain.nextStream(chatClientRequest);
        return new ChatClientMessageAggregator().aggregateChatClientResponse(chatClientResponses, this::logResponse);
    }

    private void logRequest(ChatClientRequest request) {
        logger.debug("request: {}", request);
    }

    private void logResponse(ChatClientResponse chatClientResponse) {
        logger.debug("response: {}", chatClientResponse);
    }
}
```

You can control the order of execution by setting the order value. Lower values execute first.

The `MessageAggregator` is a utility class that aggregates the Flux responses into a single `ChatClientResponse`. This is useful for logging or other processing that observes the entire response rather than individual items in the stream. Note: you cannot alter the response in the `MessageAggregator` as it is a read-only operation.

---

### Example: Re-Reading (Re2) Advisor

The "Re-Reading Improves Reasoning in Large Language Models" article introduces a technique called Re-Reading (Re2) that improves the reasoning capabilities of LLMs. The Re2 technique augments the input prompt like this:

```text
{Input_Query}
Read the question again: {Input_Query}
```

An advisor that applies the Re2 technique to the user’s input query:

```java
public class ReReadingAdvisor implements BaseAdvisor {
    private static final String DEFAULT_RE2_ADVISE_TEMPLATE = """
        {re2_input_query}
        Read the question again: {re2_input_query}
        """;

    private final String re2AdviseTemplate;
    private int order = 0;

    public ReReadingAdvisor() {
        this(DEFAULT_RE2_ADVISE_TEMPLATE);
    }

    public ReReadingAdvisor(String re2AdviseTemplate) {
        this.re2AdviseTemplate = re2AdviseTemplate;
    }

    @Override
    public ChatClientRequest before(ChatClientRequest chatClientRequest, AdvisorChain advisorChain) {
        String augmentedUserText = PromptTemplate.builder()
            .template(this.re2AdviseTemplate)
            .variables(Map.of("re2_input_query", chatClientRequest.prompt().getUserMessage().getText()))
            .build()
            .render();
        return chatClientRequest.mutate()
            .prompt(chatClientRequest.prompt().augmentUserMessage(augmentedUserText))
            .build();
    }

    @Override
    public ChatClientResponse after(ChatClientResponse chatClientResponse, AdvisorChain advisorChain) {
        return chatClientResponse;
    }

    @Override
    public int getOrder() {
        return this.order;
    }

    public ReReadingAdvisor withOrder(int order) {
        this.order = order;
        return this;
    }
}
```

The `before` method augments the user’s input query applying the Re-Reading technique. You can control the order of execution by setting the order value. Lower values execute first.

---

## Spring AI Built-in Advisors

Spring AI provides several built-in advisors to enhance your AI interactions:

- **MessageChatMemoryAdvisor**: Retrieves memory and adds it as a collection of messages to the prompt. Maintains conversation history structure. (Not all AI Models support this approach.)
- **PromptChatMemoryAdvisor**: Retrieves memory and incorporates it into the prompt’s system text.
- **VectorStoreChatMemoryAdvisor**: Retrieves memory from a VectorStore and adds it into the prompt’s system text. Useful for efficiently searching and retrieving relevant information from large datasets.
- **QuestionAnswerAdvisor**: Uses a vector store to provide question-answering capabilities, implementing the Naive RAG (Retrieval-Augmented Generation) pattern.
- **RetrievalAugmentationAdvisor**: Implements common Retrieval Augmented Generation (RAG) flows using the building blocks defined in the `org.springframework.ai.rag` package and following the Modular RAG Architecture.
- **ReReadingAdvisor**: Implements a re-reading strategy for LLM reasoning (RE2) to enhance understanding in the input phase.
- **SafeGuardAdvisor**: Prevents the model from generating harmful or inappropriate content.

---

### Streaming vs Non-Streaming

- **Non-streaming advisors** work with complete requests and responses.
- **Streaming advisors** handle requests and responses as continuous streams, using reactive programming concepts (e.g., `Flux` for responses).

Example streaming advisor:

```java
@Override
public Flux<ChatClientResponse> adviseStream(ChatClientRequest chatClientRequest, StreamAdvisorChain chain) {
    return Mono.just(chatClientRequest)
        .publishOn(Schedulers.boundedElastic())
        .map(request -> {
            // Advisor before next section
            return request;
        })
        .flatMapMany(chain::nextStream)
        .map(response -> {
            // Advisor after next section
            return response;
        });
}
```

---

### Best Practices

1. Keep advisors focused on specific tasks for better modularity.
2. Use the `adviseContext` to share state between advisors when necessary.
3. Implement both streaming and non-streaming versions of your advisor for maximum flexibility.
4. Carefully consider the order of advisors in your chain to ensure proper data flow.

---

## Breaking API Changes

### Advisor Interfaces

In 1.0 M2, there were separate `RequestAdvisor` and `ResponseAdvisor` interfaces:
- `RequestAdvisor` was invoked before the `ChatModel.call` and `ChatModel.stream` methods.
- `ResponseAdvisor` was called after these methods.

In 1.0 M3, these interfaces have been replaced with:
- `CallAroundAdvisor` → `CallAdvisor`
- `StreamAroundAdvisor` → `StreamAdvisor`
- `CallAroundAdvisorChain` → `CallAdvisorChain`
- `StreamAroundAdvisorChain` → `StreamAdvisorChain`
- `AdvisedRequest` → `ChatClientRequest`
- `AdivsedResponse` → `ChatClientResponse`

The `StreamResponseMode`, previously part of `ResponseAdvisor`, has been removed.

### Context Map Handling

**In 1.0 M2:**
- The context map was a separate method argument.
- The map was mutable and passed along the chain.

**In 1.0 M3:**
- The context map is now part of the `AdvisedRequest` and `AdvisedResponse` records.
- The map is immutable.
- To update the context, use the `updateContext` method, which creates a new unmodifiable map with the updated contents.
---
title: "Advisors API"
category: "Advisors"
source: "Advisors API __ Spring AI Reference.pdf"
generated_by: "springai-kb-converter"
---

# Advisors API

The Spring AI Advisors API provides a flexible and powerful way to intercept, modify, and enhance AI-driven interactions in your Spring applications. By leveraging the Advisors API, developers can create more sophisticated, reusable, and maintainable AI components.

The key benefits include encapsulating recurring Generative AI patterns, transforming data sent to and from Large Language Models
(LLMs), and providing portability across various models and use cases.

You can configure existing advisors using the ChatClient API as shown in the following example:

```java
ChatMemory chatMemory = ... // Initialize your chat memory store
VectorStore vectorStore = ... // Initialize your vector store

var chatClient = ChatClient.builder(chatModel)
```
```text
    .defaultAdvisors(
        MessageChatMemoryAdvisor.builder(chatMemory).build(), // chat-memory advisor
        QuestionAnswerAdvisor.builder(vectorStore).build()    // RAG advisor
    )
    .build();
```

```java
var conversationId = "678";
```

```java
String response = this.chatClient.prompt()
    // Set advisor parameters at runtime
    .advisors(advisor -> advisor.param(ChatMemory.CONVERSATION_ID, conversationId))
    .user(userText)
    .call()
.content();
```

It is recommend to register the advisors at build time using builder’s `defaultAdvisors()`  method.

Advisors also participate in the Observability stack, so you can view metrics and traces related to their execution.

Learn about Question Answer Advisor
Learn about Chat Memory Advisor

## Core Components

The API consists of `CallAdvisor`  and `CallAdvisorChain`  for non-streaming scenarios, and `StreamAdvisor`  and
`StreamAdvisorChain`  for streaming scenarios. It also includes `ChatClientRequest`  to represent the unsealed Prompt request,
`ChatClientResponse`  for the Chat Completion response. Both hold an `advise-context`  to share state across the advisor chain.
The `adviseCall()`  and the `adviseStream()`  are the key advisor methods, typically performing actions such as examining the unsealed
Prompt data, customizing and augmenting the Prompt data, invoking the next entity in the advisor chain, optionally blocking the request, examining the chat completion response, and throwing exceptions to indicate processing errors.

In addition the `getOrder()`  method determines advisor order in the chain, while `getName()`  provides a unique advisor name.

The Advisor Chain, created by the Spring AI framework, allows sequential invocation of multiple advisors ordered by their `getOrder()`  values. The lower values are executed first. The last advisor, added automatically, sends the request to the LLM.

Following flow diagram illustrates the interaction between the advisor chain and the Chat Model:
1. The Spring AI framework creates an `ChatClientRequest`  from user’s `Prompt`  along with an empty advisor `context`  object.
2. Each advisor in the chain processes the request, potentially modifying it. Alternatively, it can choose to block the request by not making
the call to invoke the next entity. In the latter case, the advisor is responsible for filling out the response.
3. The final advisor, provided by the framework, sends the request to the `Chat Model` .
4. The Chat Model’s response is then passed back through the advisor chain and converted into `ChatClientResponse` . Later includes
the shared advisor `context`  instance.
5. Each advisor can process or modify the response.
6. The final `ChatClientResponse`  is returned to the client by extracting the `ChatCompletion` .

### Advisor Order
The execution order of advisors in the chain is determined by the `getOrder()`  method. Key points to understand:

Advisors with lower order values are executed first.
The advisor chain operates as a stack:
The first advisor in the chain is the first to process the request.
It is also the last to process the response.
To control execution order:
Set the order close to `Ordered.HIGHEST_PRECEDENCE`  to ensure an advisor is executed first in the chain (first for request processing, last for response processing).
Set the order close to `Ordered.LOWEST_PRECEDENCE`  to ensure an advisor is executed last in the chain (last for request processing, first for response processing).
Higher values are interpreted as lower priority.
If multiple advisors have the same order value, their execution order is not guaranteed.

The seeming contradiction between order and execution sequence is due to the stack-like nature of the advisor chain:

An advisor with the highest precedence (lowest order value) is added to the top of the stack.
It will be the first to process the request as the stack unwinds.
It will be the last to process the response as the stack rewinds.

As a reminder, here are the semantics of the Spring `Ordered`  interface:

```java
public interface Ordered {

    /**
     * Constant for the highest precedence value.
     * @see java.lang.Integer#MIN_VALUE
     */
```
```properties
    int HIGHEST_PRECEDENCE = Integer.MIN_VALUE;
```

```java
    /**
     * Constant for the lowest precedence value.
     * @see java.lang.Integer#MAX_VALUE
     */
    int LOWEST_PRECEDENCE = Integer.MAX_VALUE;

    /**
     * Get the order value of this object.
     * <p>Higher values are interpreted as lower priority. As a consequence,
     * the object with the lowest value has the highest priority (somewhat
     * analogous to Servlet {@code load-on-startup} values).
     * <p>Same order values will result in arbitrary sort positions for the
     * affected objects.
     * @return the order value
     * @see #HIGHEST_PRECEDENCE
     * @see #LOWEST_PRECEDENCE
     */
    int getOrder();
}
```

For use cases that need to be first in the chain on both the input and output sides:

3. Use the advisor context to share state between them.

## API Overview
The main Advisor interfaces are located in the package `org.springframework.ai.chat.client.advisor.api` . Here are the key interfaces you’ll encounter when creating your own advisor:

```java
public interface Advisor extends Ordered {
```

```text
String getName();

}
```

The two sub-interfaces for synchronous and reactive Advisors are

```java
public interface CallAdvisor extends Advisor {
```

```text
ChatClientResponse adviseCall(
ChatClientRequest chatClientRequest, CallAdvisorChain callAdvisorChain);

}
```

and

```java
public interface StreamAdvisor extends Advisor {
```

```text
Flux<ChatClientResponse> adviseStream(
ChatClientRequest chatClientRequest, StreamAdvisorChain streamAdvisorChain);

}
```

To continue the chain of Advice, use `CallAdvisorChain`  and `StreamAdvisorChain`  in your Advice implementation:

The interfaces are
```java
public interface CallAdvisorChain extends AdvisorChain {

/**
 * Invokes the next {@link CallAdvisor} in the {@link CallAdvisorChain} with the given
 * request.
 */
ChatClientResponse nextCall(ChatClientRequest chatClientRequest);
```

```java
/**
 * Returns the list of all the {@link CallAdvisor} instances included in this chain at
 * the time of its creation.
 */
List<CallAdvisor> getCallAdvisors();
```

```text
}
```

and

```java
public interface StreamAdvisorChain extends AdvisorChain {

/**
 * Invokes the next {@link StreamAdvisor} in the {@link StreamAdvisorChain} with the
 * given request.
 */
Flux<ChatClientResponse> nextStream(ChatClientRequest chatClientRequest);
```

```java
/**
 * Returns the list of all the {@link StreamAdvisor} instances included in this chain
 * at the time of its creation.
 */
List<StreamAdvisor> getStreamAdvisors();
```

```text
}
```
## Implementing an Advisor

To create an advisor, implement either `CallAdvisor`  or `StreamAdvisor`  (or both). The key method to implement is `nextCall()`  for
non-streaming or `nextStream()`  for streaming advisors.

### Examples

We will provide few hands-on examples to illustrate how to implement advisors for observing and augmenting use-cases.

Logging Advisor

We can implement a simple logging advisor that logs the `ChatClientRequest`  before and the `ChatClientResponse`  after the call to the
next advisor in the chain. Note that the advisor only observes the request and response and does not modify them. This implementation
support both non-streaming and streaming scenarios.

```java
public class SimpleLoggerAdvisor implements CallAdvisor, StreamAdvisor {

private static final Logger logger = LoggerFactory.getLogger(SimpleLoggerAdvisor.class);
```

```java
@Override
public String getName() { 1
return this.getClass().getSimpleName();
}

@Override
public int getOrder() { 2
return 0;
}
```

```java
@Override
public ChatClientResponse adviseCall(ChatClientRequest chatClientRequest, CallAdvisorChain callAdvisorChain)
{
```
```text
logRequest(chatClientRequest);
```

```properties
ChatClientResponse chatClientResponse = callAdvisorChain.nextCall(chatClientRequest);
```

```text
logResponse(chatClientResponse);

return chatClientResponse;
}
```

```java
@Override
public Flux<ChatClientResponse> adviseStream(ChatClientRequest chatClientRequest,
StreamAdvisorChain streamAdvisorChain) {
logRequest(chatClientRequest);
```

```java
Flux<ChatClientResponse> chatClientResponses = streamAdvisorChain.nextStream(chatClientRequest);
```

```text
return new ChatClientMessageAggregator().aggregateChatClientResponse(chatClientResponses,
this::logResponse); 3
}
```

```java
private void logRequest(ChatClientRequest request) {
logger.debug("request: {}", request);
}

private void logResponse(ChatClientResponse chatClientResponse) {
logger.debug("response: {}", chatClientResponse);
}
```

```text
}

2
```
You can control the order of execution by setting the order value. Lower values execute first.
```text
3
```
The `MessageAggregator`  is a utility class that aggregates the Flux responses into a single ChatClientResponse. This can be useful for logging or
other processing that observe the entire response rather than individual items in the stream. Note that you can not alter the response in the
`MessageAggregator`  as it is a read-only operation.

Re-Reading (Re2) Advisor

The "Re-Reading Improves Reasoning in Large Language Models" article introduces a technique called Re-Reading (Re2) that improves
the reasoning capabilities of Large Language Models. The Re2 technique requires augmenting the input prompt like this:

```text
{Input_Query}
Read the question again: {Input_Query}
```

Implementing an advisor that applies the Re2 technique to the user’s input query can be done like this:

```java
public class ReReadingAdvisor implements BaseAdvisor {

private static final String DEFAULT_RE2_ADVISE_TEMPLATE = """
{re2_input_query}
Read the question again: {re2_input_query}
""";
```

```java
private final String re2AdviseTemplate;

private int order = 0;
```

```java
public ReReadingAdvisor() {
this(DEFAULT_RE2_ADVISE_TEMPLATE);
}

public ReReadingAdvisor(String re2AdviseTemplate) {
this.re2AdviseTemplate = re2AdviseTemplate;
}
```
```java
@Override
public ChatClientRequest before(ChatClientRequest chatClientRequest, AdvisorChain advisorChain) { 1
String augmentedUserText = PromptTemplate.builder()
.template(this.re2AdviseTemplate)
.variables(Map.of("re2_input_query", chatClientRequest.prompt().getUserMessage().getText()))
.build()
.render();
```

```text
return chatClientRequest.mutate()
.prompt(chatClientRequest.prompt().augmentUserMessage(augmentedUserText))
.build();
}
```

```java
@Override
public ChatClientResponse after(ChatClientResponse chatClientResponse, AdvisorChain advisorChain) {
return chatClientResponse;
}

@Override
public int getOrder() { 2
return this.order;
}
```

```java
public ReReadingAdvisor withOrder(int order) {
this.order = order;
return this;
}
```

```text
}

1
```
The `before`  method augments the user’s input query applying the Re-Reading technique.
```text
2
```
You can control the order of execution by setting the order value. Lower values execute first.

Spring AI Built-in Advisors
Spring AI framework provides several built-in advisors to enhance your AI interactions. Here’s an overview of the available advisors:

These advisors manage conversation history in a chat memory store:

```text
MessageChatMemoryAdvisor
```

Retrieves memory and adds it as a collection of messages to the prompt. This approach maintains the structure of the conversation history. Note, not all AI Models support this approach.

```text
PromptChatMemoryAdvisor
```

Retrieves memory and incorporates it into the prompt’s system text.

```text
VectorStoreChatMemoryAdvisor
```

Retrieves memory from a VectorStore and adds it into the prompt’s system text. This advisor is useful for efficiently searching and retrieving relevant information from large datasets.

```text
QuestionAnswerAdvisor
```

This advisor uses a vector store to provide question-answering capabilities, implementing the Naive RAG (Retrieval-Augmented
Generation) pattern.
```text
RetrievalAugmentationAdvisor

Advisor that implements common Retrieval Augmented Generation (RAG) flows using the building blocks defined
in the `org.springframework.ai.rag` package and following the Modular RAG Architecture.
```
```text
ReReadingAdvisor
```

Implements a re-reading strategy for LLM reasoning, dubbed RE2, to enhance understanding in the input phase. Based on the article:
Re-Reading Improves Reasoning in LLMs.

```text
SafeGuardAdvisor
```

A simple advisor designed to prevent the model from generating harmful or inappropriate content.

### Streaming vs Non-Streaming
Non-streaming advisors work with complete requests and responses.
Streaming advisors handle requests and responses as continuous streams, using reactive programming concepts (e.g., Flux for
responses).

```java
@Override
public Flux<ChatClientResponse> adviseStream(ChatClientRequest chatClientRequest, StreamAdvisorChain chain) {

    return  Mono.just(chatClientRequest)
            .publishOn(Schedulers.boundedElastic())
            .map(request -> {
                // This can be executed by blocking and non-blocking Threads.
                // Advisor before next section
            })
            .flatMapMany(request -> chain.nextStream(request))
            .map(response -> {
                // Advisor after next section
            });
}
```

### Best Practices

1. Keep advisors focused on specific tasks for better modularity.
2. Use the `adviseContext`  to share state between advisors when necessary.
3. Implement both streaming and non-streaming versions of your advisor for maximum flexibility.
4. Carefully consider the order of advisors in your chain to ensure proper data flow.

## Breaking API Changes

### Advisor Interfaces
In 1.0 M2, there were separate `RequestAdvisor`  and `ResponseAdvisor`  interfaces.
`RequestAdvisor`  was invoked before the `ChatModel.call`  and `ChatModel.stream`  methods.
`ResponseAdvisor`  was called after these methods.
In 1.0 M3, these interfaces have been replaced with:

```text
CallAroundAdvisor
StreamAroundAdvisor
```
The `StreamResponseMode` , previously part of `ResponseAdvisor` , has been removed.
In 1.0.0 these interfaces have been replaced:
`CallAroundAdvisor`  → `CallAdvisor` , `StreamAroundAdvisor`  → `StreamAdvisor` , `CallAroundAdvisorChain`  →
`CallAdvisorChain`  and `StreamAroundAdvisorChain`  → `StreamAdvisorChain` .
`AdvisedRequest`  → `ChatClientRequest`  and `AdivsedResponse`  → `ChatClientResponse` .

### Context Map Handling

In 1.0 M2:
The context map was a separate method argument.
The map was mutable and passed along the chain.
In 1.0 M3:
The context map is now part of the `AdvisedRequest`  and `AdvisedResponse`  records.
The map is immutable.
To update the context, use the `updateContext`  method, which creates a new unmodifiable map with the updated contents.
