---
title: "Azure OpenAI Chat"
category: "Chat"
source: "Azure OpenAI Chat __ Spring AI Reference.pdf"
generated_by: "springai-kb-converter"
---

# Azure OpenAI Chat

Azure’s OpenAI offering, powered by ChatGPT, extends beyond traditional OpenAI capabilities, delivering AI-driven text generation with enhanced functionality. Azure offers additional AI safety and responsible AI features, as highlighted in their recent update.

Azure offers Java developers the opportunity to leverage AI’s full potential by integrating it with an array of Azure services, including AI-related resources such as Vector Stores on Azure.

---

## Prerequisites

The Azure OpenAI client offers three options to connect: using an Azure API key, an OpenAI API Key, or Microsoft Entra ID.

### Azure API Key & Endpoint

To access models using an API key, obtain your Azure OpenAI `endpoint` and `api-key` from the Azure OpenAI Service section on the Azure Portal.

Spring AI defines two configuration properties:

1. `spring.ai.azure.openai.api-key`: Set this to the value of the `API Key` obtained from Azure.
2. `spring.ai.azure.openai.endpoint`: Set this to the endpoint URL obtained when provisioning your model in Azure.

You can set these configuration properties in your `application.properties` or `application.yml` file:

```properties
spring.ai.azure.openai.api-key=<your-azure-api-key>
spring.ai.azure.openai.endpoint=<your-azure-endpoint-url>
```

For enhanced security when handling sensitive information like API keys, you can use Spring Expression Language (SpEL) to reference custom environment variables:

```yaml
spring:
  ai:
    azure:
      openai:
        api-key: ${AZURE_OPENAI_API_KEY}
        endpoint: ${AZURE_OPENAI_ENDPOINT}
```

```bash
export AZURE_OPENAI_API_KEY=<your-azure-openai-api-key>
export AZURE_OPENAI_ENDPOINT=<your-azure-openai-endpoint-url>
```

### OpenAI Key

To authenticate with the OpenAI service (not Azure), provide an OpenAI API key. This will automatically set the endpoint to `api.openai.com/v1`.

When using this approach, set the `spring.ai.azure.openai.chat.options.deployment-name` property to the name of the OpenAI model you wish to use.

In your application configuration:

```properties
spring.ai.azure.openai.openai-api-key=<your-openai-key>
spring.ai.azure.openai.chat.options.deployment-name=<openai-model-name>
```

Using environment variables with SpEL:

```yaml
spring:
  ai:
    azure:
      openai:
        openai-api-key: ${AZURE_OPENAI_API_KEY}
        chat:
          options:
            deployment-name: ${AZURE_OPENAI_MODEL_NAME}
```

```bash
export AZURE_OPENAI_API_KEY=<your-openai-key>
export AZURE_OPENAI_MODEL_NAME=<openai-model-name>
```

### Microsoft Entra ID

For keyless authentication using Microsoft Entra ID (formerly Azure Active Directory), set only the `spring.ai.azure.openai.endpoint` configuration property and not the api-key property mentioned above.

If only the endpoint property is set, your application will evaluate several different options for retrieving credentials and an `OpenAIClient` instance will be created using the token credentials. It is no longer necessary to create a `TokenCredential` bean; it is configured for you automatically.

### Deployment Name

To use Azure AI applications, you need to create an Azure AI Deployment through the Azure AI Portal. In Azure, each client must specify a `Deployment Name` to connect to the Azure OpenAI service. The `Deployment Name` is different from the model you choose to deploy.

For example:

```text
Deployment Name: gpt-4o
Model Name: gpt-4o
```

If you use a different Deployment Name, update the configuration property accordingly:

```properties
spring.ai.azure.openai.chat.options.deployment-name=<my-deployment-name>
```

If you connect to OpenAI instead of Azure OpenAI by setting the `spring.ai.azure.openai.openai-api-key` property, then the `spring.ai.azure.openai.chat.options.deployment-name` is treated as an OpenAI model name.

---

### Add Repositories and BOM

Spring AI artifacts are published in Maven Central and Spring Snapshot repositories. Refer to the Artifact Repositories section to add these repositories to your build system.

To help with dependency management, Spring AI provides a BOM (bill of materials) to ensure that a consistent version of Spring AI is used throughout the entire project.

---

## Auto-configuration

Spring AI provides Spring Boot auto-configuration for the Azure OpenAI Chat Client. To enable it, add the following dependency to your project’s Maven `pom.xml` or Gradle `build.gradle` build files:

```xml
<dependency>
    <groupId>org.springframework.ai</groupId>
    <artifactId>spring-ai-starter-model-azure-openai</artifactId>
</dependency>
```

Refer to the Dependency Management section to add the Spring AI BOM to your build file.

The Azure OpenAI Chat Client is created using the OpenAIClientBuilder provided by the Azure SDK. Spring AI allows customization of the builder by providing `AzureOpenAIClientBuilderCustomizer` beans.

Example: Change the default response timeout:

```java
@Configuration
public class AzureOpenAiConfig {

    @Bean
    public AzureOpenAIClientBuilderCustomizer responseTimeoutCustomizer() {
        return openAiClientBuilder -> {
            HttpClientOptions clientOptions = new HttpClientOptions()
                .setResponseTimeout(Duration.ofMinutes(5));
            openAiClientBuilder.httpClient(HttpClient.createDefault(clientOptions));
        };
    }
}
```

---

### Chat Properties

The prefix `spring.ai.azure.openai` is the property prefix to configure the connection to Azure OpenAI.

Key properties:

| Property | Description | Default |
|---|---|---|
| spring.ai.azure.openai.api-key | The Key from Azure AI OpenAI `Keys and Endpoint` section under Resource Management |  |
| spring.ai.azure.openai.endpoint | The endpoint from the Azure AI OpenAI `Keys and Endpoint` section under Resource Management |  |
| spring.ai.azure.openai.openai-api-key | (non Azure) OpenAI API key. Used to authenticate with the OpenAI service, instead of Azure OpenAI. This automatically sets the endpoint to api.openai.com/v1. Use either `api-key` or `openai-api-key` property. With this configuration the `spring.ai.azure.openai.chat.options.deployment-name` is treated as an OpenAI Model name. |  |
| spring.ai.azure.openai.custom-headers | A map of custom headers to be included in the API requests. Each entry in the map represents a header, where the key is the header name and the value is the header | Empty map |

To enable Azure OpenAI chat model:

```properties
spring.ai.model.chat=azure-openai
```

To disable:

```properties
spring.ai.model.chat=none
```

The prefix `spring.ai.azure.openai.chat` configures the `ChatModel` implementation for Azure OpenAI.

---

### Chat Options

| Property | Description | Default |
|---|---|---|
| spring.ai.azure.openai.chat.options.deployment-name | In use with Azure, this refers to the "Deployment Name" of your model. | gpt-4o |
| spring.ai.azure.openai.chat.options.maxTokens | The maximum number of tokens to generate in the chat completion. Cannot be used with maxCompletionTokens. |  |
| spring.ai.azure.openai.chat.options.maxCompletionTokens | An upper bound for the number of tokens that can be generated for a completion, including visible output tokens and reasoning tokens. Cannot be used with maxTokens. |  |
| spring.ai.azure.openai.chat.options.temperature | The sampling temperature to use that controls the apparent creativity of generated completions. | 0.7 |
| spring.ai.azure.openai.chat.options.topP | Nucleus sampling probability mass. |  |
| spring.ai.azure.openai.chat.options.logitBias | A map between GPT token IDs and bias scores that influences the probability of specific tokens appearing in a completions response. |  |
| spring.ai.azure.openai.chat.options.user | An identifier for the caller or end user of the operation. |  |
| spring.ai.azure.openai.chat.options.stream-usage | (For streaming only) Set to add an additional chunk with token usage statistics for the entire request. | false |
| spring.ai.azure.openai.chat.options.n | The number of chat completions choices that should be generated for a chat completions response. |  |
| spring.ai.azure.openai.chat.options.stop | A collection of textual sequences that will end completions generation. |  |
| spring.ai.azure.openai.chat.options.presencePenalty | A value that influences the probability of generated tokens appearing based on their existing presence in generated text. |  |
| spring.ai.azure.openai.chat.options.responseFormat.type | Enables JSON mode or JSON schema mode for structured outputs. |  |
| spring.ai.azure.openai.chat.options.responseFormat.schema | Response format JSON schema. Applicable only for responseFormat.type=JSON_SCHEMA |  |
| spring.ai.azure.openai.chat.options.frequencyPenalty | A value that influences the probability of generated tokens appearing based on their cumulative frequency in generated text. |  |
| spring.ai.azure.openai.chat.options.tool-names | List of tools, identified by their names, to enable for function calling in a single prompt request. |  |
| spring.ai.azure.openai.chat.options.tool-callbacks | Tool Callbacks to register with the ChatModel. |  |

All properties prefixed with `spring.ai.azure.openai.chat.options` can be overridden at runtime by adding a request-specific Runtime Options.

---

### Token Limit Parameters: Model-Specific Usage

Azure OpenAI has model-specific requirements for token limiting parameters:

- **Reasoning models** (e.g., o1, o3, o4-mini series): Use `maxCompletionTokens` only. Using `maxTokens` will result in an API error.
- **Traditional models** (e.g., gpt-4o, gpt-3.5-turbo): Use `maxTokens` for output limiting. Using `maxCompletionTokens` may result in an API error.

The parameters `maxTokens` and `maxCompletionTokens` are mutually exclusive. Setting both will result in an API error from Azure OpenAI. The Spring AI Azure OpenAI client will automatically clear the previously set parameter when you set the other one, with a warning.

Example:

```java
var options = AzureOpenAiChatOptions.builder()
    .deploymentName("o1-preview")
    .maxCompletionTokens(500)  // Required for reasoning models
    .build();

var options = AzureOpenAiChatOptions.builder()
    .deploymentName("gpt-4o")
    .maxTokens(500)  // Required for non-reasoning models
    .build();
```

---

## Runtime Options

The `AzureOpenAiChatOptions` class provides model configurations, such as the model to use, the temperature, the frequency penalty, etc.

On start-up, the default options can be configured with the `AzureOpenAiChatModel(api, options)` constructor or the `spring.ai.azure.openai.chat.options.*` properties.

At runtime you can override the default options by adding new, request-specific options to the `Prompt` call. For example, to override the default model and temperature for a specific request:

```java
ChatResponse response = chatModel.call(
    new Prompt(
        "Generate the names of 5 famous pirates.",
        AzureOpenAiChatOptions.builder()
            .deploymentName("gpt-4o")
            .temperature(0.4)
        .build()
    ));
```

You can also use a portable `ChatOptions` instance, created with the `ChatOptions#builder()`.

---

## Function Calling

You can register custom Java functions with the `AzureOpenAiChatModel` and have the model intelligently choose to output a JSON object containing arguments to call one or many of the registered functions. This is a powerful technique to connect the LLM capabilities with external tools and APIs. Read more about Tool Calling.

---

## Multimodal

Multimodality refers to a model’s ability to simultaneously understand and process information from various sources, including text, images, audio, and other data formats. Presently, the Azure OpenAI `gpt-4o` model offers multimodal support.

The Azure OpenAI can incorporate a list of base64-encoded images or image URLs with the message. Spring AI’s Message interface facilitates multimodal AI models by introducing the Media type. This type encompasses data and details regarding media attachments in messages, utilizing Spring’s `org.springframework.util.MimeType` and a `java.lang.Object` for the raw media data.

Example: Fusion of user text with an image using the `GPT_4_O` model:

```java
URL url = new URL("<image-url>");
String response = ChatClient.create(chatModel).prompt()
        .options(AzureOpenAiChatOptions.builder().deploymentName("gpt-4o").build())
        .user(u -> u.text("Explain what do you see on this picture?").media(MimeTypeUtils.IMAGE_PNG, url))
        .call()
        .content();
```

You can also pass in a classpath resource instead of a URL:

```java
Resource resource = new ClassPathResource("multimodality/multimodal.test.png");
String response = ChatClient.create(chatModel).prompt()
    .options(AzureOpenAiChatOptions.builder().deploymentName("gpt-4o").build())
    .user(u -> u.text("Explain what do you see on this picture?").media(MimeTypeUtils.IMAGE_PNG, resource))
    .call()
    .content();
```

---

## Sample Controller

Create a new Spring Boot project and add the `spring-ai-starter-model-azure-openai` to your pom (or gradle) dependencies.

Add an `application.properties` file under the `src/main/resources` directory to enable and configure the OpenAI chat model:

```properties
spring.ai.azure.openai.api-key=YOUR_API_KEY
spring.ai.azure.openai.endpoint=YOUR_ENDPOINT
spring.ai.azure.openai.chat.options.deployment-name=gpt-4o
spring.ai.azure.openai.chat.options.temperature=0.7
```

Replace the `api-key` and `endpoint` with your Azure OpenAI credentials.

This will create an `AzureOpenAiChatModel` implementation that you can inject into your class. Example controller:

```java
@RestController
public class ChatController {

    private final AzureOpenAiChatModel chatModel;

    @Autowired
    public ChatController(AzureOpenAiChatModel chatModel) {
        this.chatModel = chatModel;
    }

    @GetMapping("/ai/generate")
    public Map generate(@RequestParam(value = "message", defaultValue = "Tell me a joke") String message) {
        return Map.of("generation", this.chatModel.call(message));
    }

    @GetMapping("/ai/generateStream")
    public Flux<ChatResponse> generateStream(@RequestParam(value = "message", defaultValue = "Tell me a joke") String message) {
        Prompt prompt = new Prompt(new UserMessage(message));
        return this.chatModel.stream(prompt);
    }
}
```

---

## Manual Configuration

The `AzureOpenAiChatModel` implements the `ChatModel` and `StreamingChatModel` and uses the Azure OpenAI Java Client.

To enable it, add the `spring-ai-azure-openai` dependency to your project’s Maven `pom.xml` file:

```xml
<dependency>
    <groupId>org.springframework.ai</groupId>
    <artifactId>spring-ai-azure-openai</artifactId>
</dependency>
```

Or to your Gradle `build.gradle` build file:

```groovy
dependencies {
    implementation 'org.springframework.ai:spring-ai-azure-openai'
}
```

Refer to the Dependency Management section to add the Spring AI BOM to your build file.

Next, create an `AzureOpenAiChatModel` instance and use it to generate text responses:

```java
var openAIClientBuilder = new OpenAIClientBuilder()
  .credential(new AzureKeyCredential(System.getenv("AZURE_OPENAI_API_KEY")))
  .endpoint(System.getenv("AZURE_OPENAI_ENDPOINT"));

var openAIChatOptions = AzureOpenAiChatOptions.builder()
  .deploymentName("gpt-5")
  .temperature(0.4)
  .maxCompletionTokens(200)
  .build();

var chatModel = AzureOpenAiChatModel.builder()
    .openAIClientBuilder(openAIClientBuilder)
    .defaultOptions(openAIChatOptions)
    .build();

ChatResponse response = chatModel.call(
  new Prompt("Generate the names of 5 famous pirates."));

// Or with streaming responses
Flux<ChatResponse> streamingResponses = chatModel.stream(
  new Prompt("Generate the names of 5 famous pirates."));
```

---

The `gpt-4o` is actually the `Deployment Name` as presented in the Azure AI Portal.
## Prerequisites

The Azure OpenAI client offers three options to connect: using an Azure API key or using an OpenAI API Key, or using Microsoft Entra ID.

### Azure API Key & Endpoint

To access models using an API key, obtain your Azure OpenAI `endpoint`  and `api-key`  from the Azure OpenAI Service section on the
Azure Portal.

Spring AI defines two configuration properties:

1. `spring.ai.azure.openai.api-key` : Set this to the value of the `API Key`  obtained from Azure.
2. `spring.ai.azure.openai.endpoint` : Set this to the endpoint URL obtained when provisioning your model in Azure.

You can set these configuration properties in your `application.properties`  or `application.yml`  file:

```properties
spring.ai.azure.openai.api-key=<your-azure-api-key>
spring.ai.azure.openai.endpoint=<your-azure-endpoint-url>
```

For enhanced security when handling sensitive information like API keys, you can use Spring Expression Language (SpEL) to reference
custom environment variables:

```yaml
## In application.yml
spring:
  ai:
    azure:
      openai:
        api-key: ${AZURE_OPENAI_API_KEY}
        endpoint: ${AZURE_OPENAI_ENDPOINT}
```
```bash
## In your environment or .env file
export AZURE_OPENAI_API_KEY=<your-azure-openai-api-key>
export AZURE_OPENAI_ENDPOINT=<your-azure-openai-endpoint-url>
```

### OpenAI Key

To authenticate with the OpenAI service (not Azure), provide an OpenAI API key. This will automatically set the endpoint to
api.openai.com/v1.

When using this approach, set the `spring.ai.azure.openai.chat.options.deployment-name`  property to the name of the OpenAI
model you wish to use.

In your application configuration:

```properties
spring.ai.azure.openai.openai-api-key=<your-azure-openai-key>
spring.ai.azure.openai.chat.options.deployment-name=<openai-model-name>
```

Using environment variables with SpEL:

```yaml
## In application.yml
spring:
  ai:
    azure:
      openai:
        openai-api-key: ${AZURE_OPENAI_API_KEY}
        chat:
          options:
            deployment-name: ${AZURE_OPENAI_MODEL_NAME}
```

```bash
## In your environment or .env file
export AZURE_OPENAI_API_KEY=<your-openai-key>

export AZURE_OPENAI_MODEL_NAME=<openai-model-name>
```

### Microsoft Entra ID

For keyless authentication using Microsoft Entra ID (formerly Azure Active Directory), set only the `spring.ai.azure.openai.endpoint`
configuration property and not the api-key property mentioned above.

Finding only the endpoint property, your application will evaluate several different options for retrieving credentials and an `OpenAIClient`
instance will be created using the token credentials.

It is no longer necessary to create a `TokenCredential`  bean; it is configured for you automatically.

### Deployment Name

To use Azure AI applications, you need to create an Azure AI Deployment through the Azure AI Portal. In Azure, each client must specify a
`Deployment Name`  to connect to the Azure OpenAI service. It’s important to note that the `Deployment Name`  is different from the model
you choose to deploy. For example, a deployment named 'MyAiDeployment' could be configured to use either the GPT 3.5 Turbo model or
the GPT 4.0 model.

To get started, follow these steps to create a deployment with the default settings:

```text
Deployment Name: `gpt-4o`
Model Name: `gpt-4o`
```

This Azure configuration aligns with the default configurations of the Spring Boot Azure AI Starter and its Autoconfiguration feature. If you
use a different Deployment Name, make sure to update the configuration property accordingly:

```properties
spring.ai.azure.openai.chat.options.deployment-name=<my deployment name>
```
The different deployment structures of Azure OpenAI and OpenAI leads to a property in the Azure OpenAI client library named
`deploymentOrModelName` . This is because in OpenAI there is no `Deployment Name` , only a `Model Name` .

The property `spring.ai.azure.openai.chat.options.model`  has been renamed to `spring.ai.azure.openai.chat.options.deployment-`

If you decide to connect to `OpenAI`  instead of `Azure OpenAI` , by setting the `spring.ai.azure.openai.openai-api-key=<Your OpenAI Key>`
property, then the `spring.ai.azure.openai.chat.options.deployment-name`  is treated as an OpenAI model name.

Access the OpenAI Model

You can configure the client to use directly `OpenAI`  instead of the `Azure OpenAI`  deployed models. For this you need to set the
`spring.ai.azure.openai.openai-api-key=<Your OpenAI Key>`  instead of `spring.ai.azure.openai.api-key=<Your Azure`
`OpenAi Key>` .

### Add Repositories and BOM

Spring AI artifacts are published in Maven Central and Spring Snapshot repositories. Refer to the Artifact Repositories section to add these
repositories to your build system.

To help with dependency management, Spring AI provides a BOM (bill of materials) to ensure that a consistent version of Spring AI is used
throughout the entire project. Refer to the Dependency Management section to add the Spring AI BOM to your build system.

## Auto-configuration

There has been a significant change in the Spring AI auto-configuration, starter modules' artifact names. Please refer to the upgrade notes for more
Spring AI provides Spring Boot auto-configuration for the Azure OpenAI Chat Client. To enable it add the following dependency to your
project’s Maven `pom.xml`  or Gradle `build.gradle`  build files:

```xml
<dependency>
    <groupId>org.springframework.ai</groupId>
    <artifactId>spring-ai-starter-model-azure-openai</artifactId>
</dependency>
```

Refer to the Dependency Management section to add the Spring AI BOM to your build file.

The Azure OpenAI Chat Client is created using the OpenAIClientBuilder provided by the Azure SDK. Spring AI allows to customize the
builder by providing AzureOpenAIClientBuilderCustomizer beans.

A customizer might be used for example to change the default response timeout:

```java
@Configuration
public class AzureOpenAiConfig {

@Bean
public AzureOpenAIClientBuilderCustomizer responseTimeoutCustomizer() {
return openAiClientBuilder -> {
HttpClientOptions clientOptions = new HttpClientOptions()
.setResponseTimeout(Duration.ofMinutes(5));
openAiClientBuilder.httpClient(HttpClient.createDefault(clientOptions));
};
}
```

```text
}
```

### Chat Properties
The prefix `spring.ai.azure.openai`  is the property prefix to configure the connection to Azure OpenAI.

Property
Description
Default

spring.ai.azure.openai.api-key
The Key from Azure AI OpenAI `Keys and Endpoint`  section under `Resource`
```text
Management
```

spring.ai.azure.openai.endpoint
The endpoint from the Azure AI OpenAI `Keys and Endpoint`  section under
```text
Resource Management
```

spring.ai.azure.openai.openai-api-key
(non Azure) OpenAI API key. Used to authenticate with the OpenAI service, instead of
Azure OpenAI. This automatically sets the endpoint to api.openai.com/v1. Use either
`api-key`  or `openai-api-key`  property. With this configuration the
`spring.ai.azure.openai.chat.options.deployment-name`  is treated as an
OpenAi Model name.

spring.ai.azure.openai.custom-headers
A map of custom headers to be included in the API requests. Each entry in the map
Empty map
represents a header, where the key is the header name and the value is the header

Enabling and disabling of the chat auto-configurations are now configured via top level properties with the prefix `spring.ai.model.chat` .

To enable, spring.ai.model.chat=azure-openai (It is enabled by default)

To disable, spring.ai.model.chat=none (or any value which doesn’t match azure-openai)

This change is done to allow configuration of multiple models.

The prefix `spring.ai.azure.openai.chat`  is the property prefix that configures the `ChatModel`  implementation for Azure OpenAI.
Property
Description
Default

Enable Azure OpenAI chat model.
true

spring.ai.model.chat
Enable Azure OpenAI chat model.
azure-openai

spring.ai.azure.openai.chat.options.deployment-name
In use with Azure, this refers to the "Deployment Name" of your model,
gpt-4o
which you can find at oai.azure.com/portal. It’s important to note that within
an Azure OpenAI deployment, the "Deployment Name" is distinct from the
model itself. The confusion around these terms stems from the intention to
make the Azure OpenAI client library compatible with the original OpenAI
endpoint. The deployment structures offered by Azure OpenAI and Sam
Altman’s OpenAI differ significantly. Deployments model name to provide
as part of this completions request.

spring.ai.azure.openai.chat.options.maxTokens
The maximum number of tokens to generate in the chat completion. The
total length of input tokens and generated tokens is limited by the model’s
context length. Use for non-reasoning models (e.g., gpt-4o, gpt-3.5turbo). Cannot be used with maxCompletionTokens.

spring.ai.azure.openai.chat.options.maxCompletionTokens
An upper bound for the number of tokens that can be generated for a com-
pletion, including visible output tokens and reasoning tokens. Required for
reasoning models (e.g., o1, o3, o4-mini series). Cannot be used with
maxTokens.

spring.ai.azure.openai.chat.options.temperature
The sampling temperature to use that controls the apparent creativity of
0.7
generated completions. Higher values will make output more random while
lower values will make results more focused and deterministic. It is not recommended to modify temperature and top_p for the same completions re‐
quest as the interaction of these two settings is difficult to predict.

spring.ai.azure.openai.chat.options.topP
An alternative to sampling with temperature called nucleus sampling. This
value causes the model to consider the results of tokens with the provided
probability mass.
Property
Description
Default

spring.ai.azure.openai.chat.options.logitBias
A map between GPT token IDs and bias scores that influences the proba-
bility of specific tokens appearing in a completions response. Token IDs
are computed via external tokenizer tools, while bias scores reside in the
range of -100 to 100 with minimum and maximum values corresponding to
a full ban or exclusive selection of a token, respectively. The exact behavior of a given bias score varies by model.

spring.ai.azure.openai.chat.options.user
An identifier for the caller or end user of the operation. This may be used
for tracking or rate-limiting purposes.

spring.ai.azure.openai.chat.options.stream-usage
(For streaming only) Set to add an additional chunk with token usage stafalse
tistics for the entire request. The `choices`  field for this chunk is an empty
array and all other chunks will also include a usage field, but with a null
value.

spring.ai.azure.openai.chat.options.n
The number of chat completions choices that should be generated for a
chat completions response.

spring.ai.azure.openai.chat.options.stop
A collection of textual sequences that will end completions generation.
spring.ai.azure.openai.chat.options.presencePenalty
A value that influences the probability of generated tokens appearing
based on their existing presence in generated text. Positive values will
make tokens less likely to appear when they already exist and increase the
model’s likelihood to output new topics.

spring.ai.azure.openai.chat.options.responseFormat.type
Compatible with `GPT-4o` , `GPT-4o mini` , `GPT-4 Turbo`  and all `GPT-`
`3.5 Turbo`  models newer than `gpt-3.5-turbo-1106` . The
`JSON_OBJECT`  type enables JSON mode, which guarantees the message
the model generates is valid JSON. The `JSON_SCHEMA`  type enables
Structured Outputs which guarantees the model will match your supplied
JSON schema. The `JSON_SCHEMA`  type requires setting the
`responseFormat.schema`  property as well.
Property
Description
Default

spring.ai.azure.openai.chat.options.responseFormat.schema
Response format JSON schema. Applicable only for
```properties
responseFormat.type=JSON_SCHEMA
```

spring.ai.azure.openai.chat.options.frequencyPenalty
A value that influences the probability of generated tokens appearing
based on their cumulative frequency in generated text. Positive values will
make tokens less likely to appear as their frequency increases and decrease the likelihood of the model repeating the same statements
verbatim.

spring.ai.azure.openai.chat.options.tool-names
List of tools, identified by their names, to enable for function calling in a
single prompt request. Tools with those names must exist in the
ToolCallback registry.

spring.ai.azure.openai.chat.options.tool-callbacks
Tool Callbacks to register with the ChatModel.

If false, the Spring AI will not handle the tool calls internally, but will proxy
true
them to the client. Then it is the client’s responsibility to handle the tool
calls, dispatch them to the appropriate function, and return the results. If
true (the default), the Spring AI will handle the function calls internally.
Applicable only for chat models with function calling support

All properties prefixed with `spring.ai.azure.openai.chat.options`  can be overridden at runtime by adding a request specific Runtime Options to

### Token Limit Parameters: Model-Specific Usage

Azure OpenAI has model-specific requirements for token limiting parameters:
Model Family
Required Parameter
Notes

```text
maxCompletionTokens
```
These models only accept `maxCompletionTokens` . Using `maxTokens`  will result in an API error.

```text
maxTokens
```
Traditional models use `maxTokens`  for output limiting. Using
`maxCompletionTokens`  may result in an API error.

The parameters `maxTokens`  and `maxCompletionTokens`  are mutually exclusive. Setting both parameters simultaneously will result in an API error
from Azure OpenAI. The Spring AI Azure OpenAI client will automatically clear the previously set parameter when you set the other one, with a warning

Example: Using maxCompletionTokens for reasoning models
```java
var options = AzureOpenAiChatOptions.builder()
    .deploymentName("o1-preview")
    .maxCompletionTokens(500)  // Required for reasoning models
    .build();

var options = AzureOpenAiChatOptions.builder()
    .deploymentName("gpt-4o")
    .maxTokens(500)  // Required for non-reasoning models
    .build();
```

## Runtime Options

The AzureOpenAiChatOptions.java provides model configurations, such as the model to use, the temperature, the frequency penalty, etc.

On start-up, the default options can be configured with the `AzureOpenAiChatModel(api, options)`  constructor or the
`spring.ai.azure.openai.chat.options.*`  properties.
At runtime you can override the default options by adding new, request specific, options to the `Prompt`  call. For example to override the default model and temperature for a specific request:

```java
ChatResponse response = chatModel.call(
    new Prompt(
        "Generate the names of 5 famous pirates.",
        AzureOpenAiChatOptions.builder()
            .deploymentName("gpt-4o")
            .temperature(0.4)
        .build()
    ));
```

In addition to the model specific AzureOpenAiChatOptions.java you can use a portable ChatOptions instance, created with the ChatOptions#builder().

## Function Calling

You can register custom Java functions with the AzureOpenAiChatModel and have the model intelligently choose to output a JSON object
containing arguments to call one or many of the registered functions. This is a powerful technique to connect the LLM capabilities with external tools and APIs. Read more about Tool Calling.

## Multimodal

Multimodality refers to a model’s ability to simultaneously understand and process information from various sources, including text, images,
audio, and other data formats. Presently, the Azure OpenAI `gpt-4o`  model offers multimodal support.

The Azure OpenAI can incorporate a list of base64-encoded images or image urls with the message. Spring AI’s Message interface facilitates multimodal AI models by introducing the Media type. This type encompasses data and details regarding media attachments in mes‐
sages, utilizing Spring’s `org.springframework.util.MimeType`  and a `java.lang.Object`  for the raw media data.
Below is a code example excerpted from OpenAiChatModelIT.java, illustrating the fusion of user text with an image using the `GPT_4_O`
model.

```java
URL url = new URL("
String response = ChatClient.create(chatModel).prompt()
        .options(AzureOpenAiChatOptions.builder().deploymentName("gpt-4o").build())
        .user(u -> u.text("Explain what do you see on this picture?").media(MimeTypeUtils.IMAGE_PNG, this.url))
        .call()
        .content();
```

It takes as an input the `multimodal.test.png`  image:

along with the text message "Explain what do you see on this picture?", and generates a response like this:

```text
This is an image of a fruit bowl with a simple design. The bowl is made of metal with curved wire edges that
create an open structure, allowing the fruit to be visible from all angles. Inside the bowl, there are two
yellow bananas resting on top of what appears to be a red apple. The bananas are slightly overripe, as
indicated by the brown spots on their peels. The bowl has a metal ring at the top, likely to serve as a handle
for carrying. The bowl is placed on a flat surface with a neutral-colored background that provides a clear
view of the fruit inside.
```

You can also pass in a classpath resource instead of a URL as shown in the example below
```java
Resource resource = new ClassPathResource("multimodality/multimodal.test.png");

String response = ChatClient.create(chatModel).prompt()
    .options(AzureOpenAiChatOptions.builder()
    .deploymentName("gpt-4o").build())
    .user(u -> u.text("Explain what do you see on this picture?")
    .media(MimeTypeUtils.IMAGE_PNG, this.resource))
    .call()
    .content();
```

## Sample Controller

Create a new Spring Boot project and add the `spring-ai-starter-model-azure-openai`  to your pom (or gradle) dependencies.

Add a `application.properties`  file, under the `src/main/resources`  directory, to enable and configure the OpenAi chat model:

```properties
spring.ai.azure.openai.api-key=YOUR_API_KEY
spring.ai.azure.openai.endpoint=YOUR_ENDPOINT
spring.ai.azure.openai.chat.options.deployment-name=gpt-4o
spring.ai.azure.openai.chat.options.temperature=0.7
```

replace the `api-key`  and `endpoint`  with your Azure OpenAI credentials.

This will create a `AzureOpenAiChatModel`  implementation that you can inject into your class. Here is an example of a simple
`@Controller`  class that uses the chat model for text generations.

```java
@RestController
public class ChatController {

    private final AzureOpenAiChatModel chatModel;
```
```java
    @Autowired
    public ChatController(AzureOpenAiChatModel chatModel) {
        this.chatModel = chatModel;
    }

    @GetMapping("/ai/generate")
    public Map generate(@RequestParam(value = "message", defaultValue = "Tell me a joke") String message) {
        return Map.of("generation", this.chatModel.call(message));
    }
```

```java
    @GetMapping("/ai/generateStream")
public Flux<ChatResponse> generateStream(@RequestParam(value = "message", defaultValue = "Tell me a joke")
String message) {
        Prompt prompt = new Prompt(new UserMessage(message));
        return this.chatModel.stream(prompt);
    }
}
```

## Manual Configuration

The AzureOpenAiChatModel implements the `ChatModel`  and `StreamingChatModel`  and uses the Azure OpenAI Java Client.

To enable it, add the `spring-ai-azure-openai`  dependency to your project’s Maven `pom.xml`  file:

```xml
<dependency>
    <groupId>org.springframework.ai</groupId>
    <artifactId>spring-ai-azure-openai</artifactId>
</dependency>
```

or to your Gradle `build.gradle`  build file.
```groovy
dependencies {
    implementation 'org.springframework.ai:spring-ai-azure-openai'
}
```

Refer to the Dependency Management section to add the Spring AI BOM to your build file.

The `spring-ai-azure-openai`  dependency also provide the access to the `AzureOpenAiChatModel` . For more information about the
`AzureOpenAiChatModel`  refer to the Azure OpenAI Chat section.

Next, create an `AzureOpenAiChatModel`  instance and use it to generate text responses:

```java
var openAIClientBuilder = new OpenAIClientBuilder()
  .credential(new AzureKeyCredential(System.getenv("AZURE_OPENAI_API_KEY")))
  .endpoint(System.getenv("AZURE_OPENAI_ENDPOINT"));

var openAIChatOptions = AzureOpenAiChatOptions.builder()
  .deploymentName("gpt-5")
  .temperature(0.4)
  .maxCompletionTokens(200)
  .build();
```

```java
var chatModel = AzureOpenAiChatModel.builder()
.openAIClientBuilder(openAIClientBuilder)
.defaultOptions(openAIChatOptions)
.build();

ChatResponse response = chatModel.call(
  new Prompt("Generate the names of 5 famous pirates."));
```

```java
// Or with streaming responses
```
```java
Flux<ChatResponse> streamingResponses = chatModel.stream(
  new Prompt("Generate the names of 5 famous pirates."));
```

the `gpt-4o`  is actually the `Deployment Name`  as presented in the Azure AI Portal.
