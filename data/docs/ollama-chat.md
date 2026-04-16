---
title: "Ollama Chat"
category: "Chat"
source: "Ollama Chat __ Spring AI Reference.pdf"
generated_by: "springai-kb-converter"
---

# Ollama Chat

Ollama lets you run large language models locally. Spring AI integrates with Ollama through `OllamaChatModel` for both synchronous and streaming chat completion.

## Prerequisites

Before using the chat model, make sure you have access to an Ollama instance.

Common setup options include:

- local Ollama installation
- Testcontainers-based Ollama setup
- Kubernetes service binding to a remote Ollama instance

Pull a model before use:

```bash
ollama pull <model-name>
```

You can also use GGUF models from Hugging Face:

```bash
ollama pull hf.co/<username>/<model-repository>
```

## Spring Boot Auto-Configuration

Add the Ollama starter dependency:

```xml
<dependency>
   <groupId>org.springframework.ai</groupId>
   <artifactId>spring-ai-starter-model-ollama</artifactId>
</dependency>
```

Use the `spring.ai.ollama` prefix for Ollama connection and model settings.

### Core Properties

```yaml
spring:
  ai:
    ollama:
      base-url: http://localhost:11434
      chat:
        options:
          model: mistral
          temperature: 0.7
```

Top-level model enablement uses `spring.ai.model.chat`:

- `ollama` to enable
- `none` (or another value) to disable

## Runtime Options

Default options can be set through configuration or via `OllamaChatModel` construction.

Request-level overrides can be passed with `OllamaChatOptions` inside each `Prompt`.

```java
ChatResponse response = chatModel.call(
    new Prompt(
        "Generate the names of 5 famous pirates.",
        OllamaChatOptions.builder()
            .model(OllamaModel.LLAMA3_1)
            .temperature(0.4)
            .build()
    )
);
```

## Auto-Pulling Models

Spring AI can pull missing models at startup.

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

You can also preload additional chat models:

```yaml
spring:
  ai:
    ollama:
      init:
        pull-model-strategy: when_missing
        chat:
          additional-models:
            - llama3.2
            - qwen2.5
```

For production, pre-pulling models outside startup is usually preferable to avoid long boot times.

## Tool Calling

Ollama tool calling is supported through Spring AI tool callback integration.

Use Ollama `0.2.8+` for tool calling and `0.4.6+` for streaming tool-calling scenarios.

## Thinking Mode

Thinking-capable models can emit reasoning content before the final answer.

Examples include Qwen3, DeepSeek R1, DeepSeek v3.1, and GPT-OSS variants.

### Enable or Disable Thinking

```java
ChatResponse response = chatModel.call(
    new Prompt(
        "How many letter 'r' are in the word 'strawberry'?",
        OllamaChatOptions.builder()
            .model("qwen3")
            .enableThinking()
            .build()
    )
);

String thinking = response.getResult().getMetadata().get("thinking");
String answer = response.getResult().getOutput().getText();
```

Disable explicitly:

```java
ChatResponse response = chatModel.call(
    new Prompt(
        "What is 2+2?",
        OllamaChatOptions.builder()
            .model("deepseek-r1")
            .disableThinking()
            .build()
    )
);
```

### GPT-OSS Thinking Levels

GPT-OSS supports explicit thinking levels:

- `.thinkLow()`
- `.thinkMedium()`
- `.thinkHigh()`

```java
ChatResponse response = chatModel.call(
    new Prompt(
        "Solve this complex problem",
        OllamaChatOptions.builder()
            .model("gpt-oss")
            .thinkHigh()
            .build()
    )
);
```

### Streaming with Thinking

```java
Flux<ChatResponse> stream = chatModel.stream(
    new Prompt(
        "Explain quantum entanglement",
        OllamaChatOptions.builder()
            .model("qwen3")
            .enableThinking()
            .build()
    )
);

stream.subscribe(response -> {
    String thinking = response.getResult().getMetadata().get("thinking");
    String content = response.getResult().getOutput().getText();

    if (thinking != null && !thinking.isEmpty()) {
        System.out.println("[Thinking] " + thinking);
    }
    if (content != null && !content.isEmpty()) {
        System.out.println("[Response] " + content);
    }
});
```

When thinking is disabled or unsupported, the `thinking` metadata field is empty or absent.

## Multimodal Chat

Ollama models such as LLaVA and BakLLaVA support multimodal input.

Spring AI uses `Media` on `UserMessage` to attach images (and other media types where model support exists).

```java
var imageResource = new ClassPathResource("/multimodal.test.png");

var userMessage = new UserMessage(
    "Explain what do you see on this picture?",
    new Media(MimeTypeUtils.IMAGE_PNG, imageResource)
);

ChatResponse response = chatModel.call(
    new Prompt(userMessage,
        OllamaChatOptions.builder().model(OllamaModel.LLAVA).build())
);
```

## Structured Outputs

Ollama supports structured outputs through the `format`/schema mechanism.

### Simple JSON Mode

Use `.format("json")` when any valid JSON shape is acceptable.

```java
ChatResponse response = chatModel.call(
    new Prompt(
        "List 3 countries in Europe",
        OllamaChatOptions.builder()
            .model("llama3.2")
            .format("json")
            .build()
    )
);
```

### JSON Schema Mode

Use `.outputSchema(...)` for predictable response structure.

```java
String jsonSchema = """
{
  "type": "object",
  "properties": {
    "countries": {
      "type": "array",
      "items": { "type": "string" }
    }
  },
  "required": ["countries"]
}
""";

ChatResponse response = chatModel.call(
    new Prompt(
        "List 3 countries in Europe",
        OllamaChatOptions.builder()
            .model("llama3.2")
            .outputSchema(jsonSchema)
            .build()
    )
);
```

You can also generate schema via `BeanOutputConverter` and map the response back to strongly typed objects.

## OpenAI API Compatibility

Ollama exposes an OpenAI-compatible endpoint. You can use Spring AI OpenAI client integration against Ollama by pointing OpenAI base URL to the Ollama server and choosing an Ollama model name.

This path also supports reasoning content for thinking-capable models via metadata such as `reasoningContent`.

## Sample Controller

```java
@RestController
public class ChatController {

    private final OllamaChatModel chatModel;

    public ChatController(OllamaChatModel chatModel) {
        this.chatModel = chatModel;
    }

    @GetMapping("/ai/generate")
    public Map<String, String> generate(
            @RequestParam(value = "message", defaultValue = "Tell me a joke") String message) {
        return Map.of("generation", chatModel.call(message));
    }

    @GetMapping("/ai/generateStream")
    public Flux<ChatResponse> generateStream(
            @RequestParam(value = "message", defaultValue = "Tell me a joke") String message) {
        Prompt prompt = new Prompt(new UserMessage(message));
        return chatModel.stream(prompt);
    }
}
```

## Manual Configuration

If you do not want Spring Boot auto-configuration, create `OllamaApi` and `OllamaChatModel` manually.

```java
var ollamaApi = OllamaApi.builder().build();

var chatModel = OllamaChatModel.builder()
        .ollamaApi(ollamaApi)
        .defaultOptions(
            OllamaChatOptions.builder()
                .model(OllamaModel.MISTRAL)
                .temperature(0.9)
                .build())
        .build();

ChatResponse response = chatModel.call(
    new Prompt("Generate the names of 5 famous pirates.")
);

Flux<ChatResponse> stream = chatModel.stream(
    new Prompt("Generate the names of 5 famous pirates.")
);
```

## Low-Level API

`OllamaApi` is the low-level client. For application code, prefer `OllamaChatModel` unless you need direct protocol control.

```java
OllamaApi ollamaApi = new OllamaApi("http://localhost:11434");

var request = ChatRequest.builder("orca-mini")
    .stream(false)
    .messages(List.of(
        Message.builder(Role.SYSTEM)
            .content("You are a geography teacher.")
            .build(),
        Message.builder(Role.USER)
            .content("What is the capital of Bulgaria?")
            .build()))
    .options(OllamaChatOptions.builder().temperature(0.9).build())
    .build();

ChatResponse response = ollamaApi.chat(request);
```

## Notes

- Keep model and option selection per-request when you need dynamic behavior.
- Prefer pre-pulled models in production.
- Use thinking mode only with models that support reasoning output.
- For structured output in production, prefer `outputSchema(...)` over free-form JSON mode.
