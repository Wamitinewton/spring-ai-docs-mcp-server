---
title: "Structured Output Converter"
category: "Structured Output"
source: "Structured Output Converter __ Spring AI Reference.pdf"
generated_by: "springai-kb-converter"
---

# Structured Output Converter

The ability of LLMs to produce structured outputs is important for downstream applications that depend on reliable parsing.
Developers often need to convert AI model results into data types such as JSON, XML, or Java classes that can be passed to other application components.

Spring AI `Structured Output Converters` help transform LLM output into structured formats.

Generating structured outputs from generic completion APIs requires careful handling of both inputs and outputs. The structured output converter plays a key role before and after the LLM call.

Before the LLM call, the converter appends format instructions to the prompt so the model can generate output in the desired structure.

As more AI models natively support structured outputs, you can leverage this with `AdvisorParams.ENABLE_NATIVE_STRUCTURED_OUTPUT`.
This approach uses the generated JSON schema directly with the model's native structured output API, avoiding prompt-level format instructions and improving reliability.

After the LLM call, the converter parses the model output text and maps it to the requested structured type (for example JSON, XML, or domain-specific structures).

`StructuredOutputConverter` is a best-effort mechanism. The model is not guaranteed to return exactly the requested structure, so you should implement validation as needed.

`StructuredOutputConverter` is not used for LLM tool calling, since tool calling already provides structured outputs.

## Structured Output API

The `StructuredOutputConverter` interface allows structured output mapping from text-based model output.

```java
public interface StructuredOutputConverter<T> extends Converter<String, T>, FormatProvider {
}
```

It combines Spring's `Converter<String, T>` and `FormatProvider`:

```java
public interface FormatProvider {
    String getFormat();
}
```

`FormatProvider` supplies formatting guidance so the AI model can generate output that can be converted to target type `T` by `Converter`.

Example format instructions:

```text
Your response should be in JSON format.
The data structure for the JSON should match this Java class: java.util.HashMap
Do not include any explanations, only provide a RFC8259 compliant JSON response following this format without deviation.
```

Format instructions are usually appended to user input through `PromptTemplate`:

```java
StructuredOutputConverter<?> outputConverter = ...;
String userInputTemplate = """
    ... user text input ....
    {format}
    """;

Prompt prompt = new Prompt(
    PromptTemplate.builder()
        .template(userInputTemplate)
        .variables(Map.of("format", outputConverter.getFormat()))
        .build()
        .createMessage()
);
```

`Converter<String, T>` is responsible for transforming model output text into instances of type `T`.

### Available Converters

Spring AI currently provides these implementations:

- `AbstractConversionServiceOutputConverter<T>`: Offers a pre-configured `GenericConversionService` for transforming LLM output. No default `FormatProvider` implementation.
- `AbstractMessageOutputConverter<T>`: Supplies a pre-configured `MessageConverter` for transforming LLM output. No default `FormatProvider` implementation.
- `BeanOutputConverter<T>`: Configured with a Java class or `ParameterizedTypeReference`. Uses a `FormatProvider` that instructs the model to produce JSON compliant with a `DRAFT_2020_12` JSON Schema derived from the target type, then deserializes using `ObjectMapper`.
- `MapOutputConverter`: Extends `AbstractMessageOutputConverter` and guides the model to produce RFC8259-compliant JSON, then converts to `java.util.Map<String, Object>`.
- `ListOutputConverter`: Extends `AbstractConversionServiceOutputConverter` and provides comma-delimited list formatting, converting output into `java.util.List`.

## Using Converters

The following sections show how to use the available converters for structured outputs.

### Bean Output Converter

The following example uses `BeanOutputConverter` to generate an actor filmography.

Target record:

```java
record ActorsFilms(String actor, List<String> movies) {
}
```

Using the high-level fluent `ChatClient` API:

```java
ActorsFilms actorsFilms = ChatClient.create(chatModel).prompt()
    .user(u -> u.text("Generate the filmography of 5 movies for {actor}.")
        .param("actor", "Tom Hanks"))
    .call()
    .entity(ActorsFilms.class);
```

Using the low-level `ChatModel` API:

```java
BeanOutputConverter<ActorsFilms> beanOutputConverter =
    new BeanOutputConverter<>(ActorsFilms.class);

String format = beanOutputConverter.getFormat();
String actor = "Tom Hanks";

String template = """
    Generate the filmography of 5 movies for {actor}.
    {format}
    """;

Generation generation = chatModel.call(
    PromptTemplate.builder()
        .template(template)
        .variables(Map.of("actor", actor, "format", format))
        .build()
        .create()
).getResult();

ActorsFilms actorsFilms = beanOutputConverter.convert(generation.getOutput().getText());
```

### Property Ordering in Generated Schema

`BeanOutputConverter` supports custom property ordering in generated JSON schema via `@JsonPropertyOrder`.

Example:

```java
@JsonPropertyOrder({"actor", "movies"})
record ActorsFilms(String actor, List<String> movies) {}
```

This annotation works with both records and regular Java classes.

### Generic Bean Types

Use the `ParameterizedTypeReference` constructor for complex target types such as lists.

Using `ChatClient`:

```java
List<ActorsFilms> actorsFilms = ChatClient.create(chatModel).prompt()
    .user("Generate the filmography of 5 movies for Tom Hanks and Bill Murray.")
    .call()
    .entity(new ParameterizedTypeReference<List<ActorsFilms>>() {});
```

Using `ChatModel`:

```java
BeanOutputConverter<List<ActorsFilms>> outputConverter = new BeanOutputConverter<>(
    new ParameterizedTypeReference<List<ActorsFilms>>() {}
);

String format = outputConverter.getFormat();
String template = """
    Generate the filmography of 5 movies for Tom Hanks and Bill Murray.
    {format}
    """;

Prompt prompt = PromptTemplate.builder()
    .template(template)
    .variables(Map.of("format", format))
    .build()
    .create();

Generation generation = chatModel.call(prompt).getResult();
List<ActorsFilms> actorsFilms = outputConverter.convert(generation.getOutput().getText());
```

### Map Output Converter

The following snippet uses `MapOutputConverter` to convert model output into a map.

Using `ChatClient`:

```java
Map<String, Object> result = ChatClient.create(chatModel).prompt()
    .user(u -> u.text("Provide me a List of {subject}")
        .param("subject", "an array of numbers from 1 to 9 under the key name 'numbers'"))
    .call()
    .entity(new ParameterizedTypeReference<Map<String, Object>>() {});
```

Using `ChatModel`:

```java
MapOutputConverter mapOutputConverter = new MapOutputConverter();

String format = mapOutputConverter.getFormat();
String template = """
    Provide me a List of {subject}
    {format}
    """;

Prompt prompt = PromptTemplate.builder()
    .template(template)
    .variables(Map.of(
        "subject", "an array of numbers from 1 to 9 under the key name 'numbers'",
        "format", format
    ))
    .build()
    .create();

Generation generation = chatModel.call(prompt).getResult();
Map<String, Object> result = mapOutputConverter.convert(generation.getOutput().getText());
```

### List Output Converter

The following snippet uses `ListOutputConverter` to convert model output into a list of ice cream flavors.

Using `ChatClient`:

```java
List<String> flavors = ChatClient.create(chatModel).prompt()
    .user(u -> u.text("List five {subject}")
        .param("subject", "ice cream flavors"))
    .call()
    .entity(new ListOutputConverter(new DefaultConversionService()));
```

Using `ChatModel`:

```java
ListOutputConverter listOutputConverter = new ListOutputConverter(new DefaultConversionService());

String format = listOutputConverter.getFormat();
String template = """
    List five {subject}
    {format}
    """;

Prompt prompt = PromptTemplate.builder()
    .template(template)
    .variables(Map.of("subject", "ice cream flavors", "format", format))
    .build()
    .create();

Generation generation = chatModel.call(prompt).getResult();
List<String> list = listOutputConverter.convert(generation.getOutput().getText());
```

## Native Structured Output

Many modern AI models now provide native support for structured output, which is typically more reliable than prompt-based formatting.
Spring AI supports this through Native Structured Output.

When native structured output is enabled, the JSON schema generated by `BeanOutputConverter` is sent directly to the model's structured output API.
This removes the need to append format instructions to prompts.

Benefits:

- Higher reliability: Model output conforms to schema more consistently
- Cleaner prompts: No explicit format instructions required
- Better performance: Model can optimize for structured output internally

### Using Native Structured Output

Enable native structured output using `AdvisorParams.ENABLE_NATIVE_STRUCTURED_OUTPUT`:

```java
ActorsFilms actorsFilms = ChatClient.create(chatModel).prompt()
    .advisors(AdvisorParams.ENABLE_NATIVE_STRUCTURED_OUTPUT)
    .user("Generate the filmography for a random actor.")
    .call()
    .entity(ActorsFilms.class);
```

You can also set it globally with `defaultAdvisors()` on `ChatClient.Builder`:

```java
@Bean
ChatClient chatClient(ChatClient.Builder builder) {
    return builder
        .defaultAdvisors(AdvisorParams.ENABLE_NATIVE_STRUCTURED_OUTPUT)
        .build();
}
```

### Supported Models for Native Structured Output

The following model families currently support native structured output:

- OpenAI: GPT-4o and later models with JSON Schema support
- Anthropic: Claude 3.5 Sonnet and later models
- Vertex AI Gemini: Gemini 1.5 Pro and later models
- Mistral AI: Mistral Small and later models with JSON Schema support

Some models (for example OpenAI in specific modes) may not support arrays of objects at the top level.
In such cases, use Spring AI default structured output conversion without the native structured output advisor.

## Built-in JSON Mode

Some AI models provide dedicated options for structured (usually JSON) output.

- OpenAI: `spring.ai.openai.chat.options.responseFormat`
  - `JSON_OBJECT`: guarantees valid JSON output
  - `JSON_SCHEMA`: with supplied schema, guarantees schema-matching output
- Azure OpenAI: `spring.ai.azure.openai.chat.options.responseFormat`
  - `{ "type": "json_object" }` enables JSON mode and guarantees valid JSON
- Ollama: `spring.ai.ollama.chat.options.format`
  - Currently supported value: `json`
- Mistral AI: `spring.ai.mistralai.chat.options.responseFormat`
  - `{ "type": "json_object" }` enables JSON mode
  - `{ "type": "json_schema" }` with schema enables native structured output
