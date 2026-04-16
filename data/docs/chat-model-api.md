---
title: "Chat Model API"
category: "Chat"
source: "Chat Model API __ Spring AI Reference.pdf"
generated_by: "springai-kb-converter"
---

# Chat Model API

The Spring AI Chat Model API provides a portable interface for chat completion across multiple AI providers.

It is designed around consistent abstractions so you can:

- switch models with minimal code changes,
- use the same prompt/response structure across providers,
- combine default startup options with per-request overrides.

## Core Concepts

### ChatModel

`ChatModel` is the synchronous chat interface.

```java
public interface ChatModel extends Model<Prompt, ChatResponse>, StreamingChatModel {

    default String call(String message) { ... }

    @Override
    ChatResponse call(Prompt prompt);
}
```

- `call(String message)` is a convenience entry point.
- `call(Prompt prompt)` is the primary method for production use.

### StreamingChatModel

`StreamingChatModel` returns incremental results via Reactor `Flux`.

```java
public interface StreamingChatModel extends StreamingModel<Prompt, ChatResponse> {

    default Flux<String> stream(String message) { ... }

    @Override
    Flux<ChatResponse> stream(Prompt prompt);
}
```

### Prompt

`Prompt` is a model request that wraps:

- a list of `Message` instructions,
- optional model options (`ChatOptions`).

```java
public class Prompt implements ModelRequest<List<Message>> {

    private final List<Message> messages;
    private ChatOptions modelOptions;

    @Override
    public ChatOptions getOptions() { ... }

    @Override
    public List<Message> getInstructions() { ... }
}
```

### Message and Message Types

A `Message` includes text, metadata, and a role (`MessageType`).

```java
public interface Content {
    String getText();
    Map<String, Object> getMetadata();
}

public interface Message extends Content {
    MessageType getMessageType();
}
```

Multimodal messages can additionally implement `MediaContent`.

```java
public interface MediaContent extends Content {
    Collection<Media> getMedia();
}
```

`MessageType` corresponds to conversational role semantics (for example: system, user, assistant, tool/function).

### ChatOptions

`ChatOptions` defines portable model controls. Provider-specific options are supported by each concrete implementation.

```java
public interface ChatOptions extends ModelOptions {
    String getModel();
    Float getFrequencyPenalty();
    Integer getMaxTokens();
    Float getPresencePenalty();
    List<String> getStopSequences();
    Float getTemperature();
    Integer getTopK();
    Float getTopP();
    ChatOptions copy();
}
```

## Option Resolution Model

Spring AI combines configuration from two levels:

1. Startup defaults configured on `ChatModel` / `StreamingChatModel`
2. Runtime request options provided via `Prompt`

Merge behavior:

- Runtime options override startup defaults when both are present.
- The framework converts prompt input into provider-native request payloads.
- Provider output is normalized to `ChatResponse`.

This gives a balance between global defaults and request-level customization.

## Response Model

### ChatResponse

`ChatResponse` is the normalized model response container.

```java
public class ChatResponse implements ModelResponse<Generation> {

    private final ChatResponseMetadata chatResponseMetadata;
    private final List<Generation> generations;

    @Override
    public ChatResponseMetadata getMetadata() { ... }

    @Override
    public List<Generation> getResults() { ... }
}
```

It contains:

- metadata (`ChatResponseMetadata`),
- one or more `Generation` outputs.

### Generation

A `Generation` represents one assistant output and its metadata.

```java
public class Generation implements ModelResult<AssistantMessage> {

    private final AssistantMessage assistantMessage;
    private ChatGenerationMetadata chatGenerationMetadata;

    @Override
    public AssistantMessage getOutput() { ... }

    @Override
    public ChatGenerationMetadata getMetadata() { ... }
}
```

## Available Implementations

Spring AI exposes a unified API over multiple chat providers. Availability of streaming, multimodality, and tool/function support depends on the provider/model.

Typical implementations include:

- OpenAI chat completion
- Azure OpenAI chat completion
- Ollama chat completion
- Hugging Face chat completion
- Google Vertex AI Gemini chat completion
- Amazon Bedrock chat models
- Mistral AI chat completion
- Anthropic chat completion

For capability details, refer to the model comparison documentation in this repository.

## Position in Spring AI

The Chat Model API is built on top of the generic Spring AI model abstractions and provides chat-specific request/response semantics.

This architecture enables:

- consistent client code,
- provider portability,
- access to both portable and provider-specific options.
