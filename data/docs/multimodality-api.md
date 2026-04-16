---
title: "Multimodality API"
category: "Multimodality"
source: "Multimodality API __ Spring AI Reference.pdf"
generated_by: "springai-kb-converter"
---

# Multimodality API

Spring AI supports multimodal models that can process text together with other modalities such as images, audio, and video.

The Spring AI message API provides the abstractions needed to attach media to user messages and send multimodal prompts to supported chat models.

## What Multimodality Means

Multimodality refers to a model’s ability to interpret and combine information from multiple input types.

In practice, that means you can send text plus media in the same request and ask the model to reason over both.

The media channel is primarily used with `UserMessage`. System messages do not usually carry media, and assistant responses are still text-oriented in the standard chat API.

## Message Model

A multimodal request is typically built from a `UserMessage` that contains text plus one or more media entries.

The media payload can be backed by a Spring `Resource` or a URI, and each item is identified by a `MimeType`.

```java
var imageResource = new ClassPathResource("/multimodal.test.png");

var userMessage = UserMessage.builder()
        .text("Explain what do you see in this picture?")
        .media(new Media(MimeTypeUtils.IMAGE_PNG, imageResource))
        .build();

ChatResponse response = chatModel.call(new Prompt(userMessage));
```

The same request can also be expressed with the fluent `ChatClient` API:

```java
String response = ChatClient.create(chatModel)
        .prompt()
        .user(user -> user
                .text("Explain what do you see in this picture?")
                .media(MimeTypeUtils.IMAGE_PNG, new ClassPathResource("/multimodal.test.png")))
        .call()
        .content();
```

## Supported Models

Spring AI multimodal support depends on the underlying provider and model.

Examples of supported multimodal families include:

- Anthropic Claude 3
- AWS Bedrock Converse
- Azure OpenAI, including GPT-4o models
- Mistral AI, including Pixtral models
- Ollama, including LLaVA, BakLLaVA, and Llama 3.2 models
- OpenAI, including GPT-4 and GPT-4o models
- Vertex AI Gemini, including gemini-1.5-pro-001 and gemini-1.5-flash-001

Always check the provider documentation for the exact media types and limits supported by a given model.

## Typical Workflow

A multimodal interaction usually follows this pattern:

1. load or reference the media input,
2. build a `UserMessage` with text and media,
3. send the prompt through `ChatModel` or `ChatClient`,
4. read the text response from the model.

## Example Response

A multimodal model might return a response like this when asked to describe an image:

> This is an image of a fruit bowl with a simple design. The bowl is made of metal with curved wire edges that create an open structure, allowing the fruit to be visible from all angles. Inside the bowl, there are two yellow bananas resting on top of what appears to be a red apple. The bananas are slightly overripe, as indicated by the brown spots on their peels.

## Notes

- Multimodal support is provider-specific.
- Media input is typically attached to user messages.
- The exact media formats supported by each model vary.
- Assistant outputs in the standard chat API remain text-based.
