---
title: "Prompts"
category: "Prompts"
source: "Prompts __ Spring AI Reference.pdf"
generated_by: "springai-kb-converter"
---

# Prompts

Prompts are the primary input to an AI model. The quality, structure, and context of the prompt strongly influence response quality.

In Spring AI, prompting is built around structured message objects and templating utilities that make dynamic prompt generation safer and easier to maintain.

## Core Concepts

### Prompt

`Prompt` is a container for:

- one or more `Message` instances
- optional request options (`ChatOptions`)

It is the main input type for `ChatModel.call(...)`.

```java
public class Prompt implements ModelRequest<List<Message>> {

    private final List<Message> messages;
    private ChatOptions chatOptions;
}
```

### Message

`Message` represents one conversation item with a role and content.

```java
public interface Content {
    String getContent();
    Map<String, Object> getMetadata();
}

public interface Message extends Content {
    MessageType getMessageType();
}
```

Multimodal messages can also carry media:

```java
public interface MediaContent extends Content {
    Collection<Media> getMedia();
}
```

### Message Roles

Spring AI uses the following role model:

- `SYSTEM`: instructions and behavior constraints
- `USER`: user request content
- `ASSISTANT`: model response content
- `TOOL`: tool/function response content

```java
public enum MessageType {
    USER("user"),
    ASSISTANT("assistant"),
    SYSTEM("system"),
    TOOL("tool");
}
```

## PromptTemplate

`PromptTemplate` supports variable substitution and structured prompt construction.

```java
public class PromptTemplate implements PromptTemplateActions, PromptTemplateMessageActions {
}
```

By default, Spring AI uses `StTemplateRenderer` (StringTemplate-based rendering) with `{...}` placeholders.

You can customize delimiters to avoid collisions with JSON-heavy prompts.

```java
PromptTemplate promptTemplate = PromptTemplate.builder()
    .renderer(StTemplateRenderer.builder()
        .startDelimiterToken('<')
        .endDelimiterToken('>')
        .build())
    .template("""
            Tell me the names of 5 movies whose soundtrack was composed by <composer>.
            """)
    .build();

String prompt = promptTemplate.render(Map.of("composer", "John Williams"));
```

## PromptTemplate Action Interfaces

`PromptTemplate` exposes multiple action styles:

- string rendering
- message creation
- prompt creation

### String Rendering

```java
public interface PromptTemplateStringActions {
    String render();
    String render(Map<String, Object> model);
}
```

### Message Creation

```java
public interface PromptTemplateMessageActions {
    Message createMessage();
    Message createMessage(List<Media> mediaList);
    Message createMessage(Map<String, Object> model);
}
```

### Prompt Creation

```java
public interface PromptTemplateActions extends PromptTemplateStringActions {
    Prompt create();
    Prompt create(ChatOptions modelOptions);
    Prompt create(Map<String, Object> model);
    Prompt create(Map<String, Object> model, ChatOptions modelOptions);
}
```

## Example Usage

### Basic Prompt Template

```java
PromptTemplate promptTemplate = new PromptTemplate("Tell me a {adjective} joke about {topic}");

Prompt prompt = promptTemplate.create(Map.of("adjective", "funny", "topic", "pirates"));
Generation result = chatModel.call(prompt).getResult();
```

### Combining System and User Messages

```java
String userText = """
    Tell me about three famous pirates from the Golden Age of Piracy.
    Write at least a sentence for each pirate.
    """;

Message userMessage = new UserMessage(userText);

String systemText = """
    You are a helpful AI assistant.
    Your name is {name}.
    Reply in the style of a {voice}.
    """;

SystemPromptTemplate systemPromptTemplate = new SystemPromptTemplate(systemText);
Message systemMessage = systemPromptTemplate.createMessage(Map.of("name", "Nora", "voice", "historian"));

Prompt prompt = new Prompt(List.of(systemMessage, userMessage));
List<Generation> response = chatModel.call(prompt).getResults();
```

### Using Resource-Based Prompt Templates

```java
@Value("classpath:/prompts/system-message.st")
private Resource systemResource;

SystemPromptTemplate systemPromptTemplate = new SystemPromptTemplate(systemResource);
```

## Prompt Engineering Guidance

Effective prompts usually combine four elements:

- clear instructions
- relevant external context
- concrete user input
- explicit output expectations

Useful techniques include:

- text summarization
- question answering
- text classification
- conversation framing
- code generation
- zero-shot and few-shot prompting
- chain-of-thought style decomposition
- reason-and-act workflows

For structured outputs, prefer schema-driven constraints or Spring AI structured output converters when available.

## Token Awareness

Tokens are how models process text internally.

Practical implications:

- billing often scales with input and output token count
- model context windows cap how much input can be processed at once
- unnecessary context increases cost and can reduce response quality

Prompt quality is not only about wording, but also about selecting only the context needed for the task.

## Notes

- Use `PromptTemplate` for dynamic prompt generation.
- Prefer explicit roles (`SYSTEM`, `USER`, `TOOL`) for multi-turn consistency.
- Use custom delimiters when prompt content includes JSON templates.
- Keep prompts concise and context-relevant for cost and quality control.
