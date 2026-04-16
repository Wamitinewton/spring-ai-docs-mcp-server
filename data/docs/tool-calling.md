---
title: "Tool Calling"
category: "Tool Calling"
source: "Tool Calling __ Spring AI Reference.pdf"
generated_by: "springai-kb-converter"
---

# Tool Calling

Tool calling (also known as function calling) allows a model to interact with external APIs or tools to augment its capabilities.

Tools are mainly used for:

- Information retrieval: querying external sources (database, web service, filesystem, search) to provide context the model does not have.
- Taking action: executing operations in software systems (send email, create record, submit form, trigger workflow).

Although tool calling is often described as a model capability, the client application executes the tools. The model can only request a tool call and provide arguments. The application resolves the tool, executes it, and returns results. The model never directly accesses your APIs.

Spring AI provides APIs to define tools, resolve tool-call requests, and execute tools.

See also:

- Chat Model Comparisons (for model-level support)
- Migration guide from deprecated `FunctionCallback` to `ToolCallback`

## Quick Start

This quick start demonstrates two tools:

- Information retrieval tool: get current date and time in user timezone
- Action tool: set an alarm for a specified time

### Information Retrieval

Models do not have real-time awareness by default. A tool can supply that context.

```java
class DateTimeTools {

    @Tool(description = "Get the current date and time in the user's timezone")
    String getCurrentDateTime() {
        return LocalDateTime.now().atZone(LocaleContextHolder.getTimeZone().toZoneId()).toString();
    }
}
```

Make the tool available through `ChatClient`:

```java
ChatModel chatModel = ...;

String response = ChatClient.create(chatModel)
    .prompt("What day is tomorrow?")
    .tools(new DateTimeTools())
    .call()
    .content();

System.out.println(response);
```

Example output:

```text
Tomorrow is 2015-10-21.
```

Without the tool, the model typically responds that it cannot access real-time information.

### Taking Actions

Tools can also execute actions produced by model reasoning.

```java
class DateTimeTools {

    @Tool(description = "Get the current date and time in the user's timezone")
    String getCurrentDateTime() {
        return LocalDateTime.now().atZone(LocaleContextHolder.getTimeZone().toZoneId()).toString();
    }

    @Tool(description = "Set a user alarm for the given time, provided in ISO-8601 format")
    void setAlarm(String time) {
        LocalDateTime alarmTime = LocalDateTime.parse(time, DateTimeFormatter.ISO_DATE_TIME);
        System.out.println("Alarm set for " + alarmTime);
    }
}
```

Use both tools in one request:

```java
ChatModel chatModel = ...;

String response = ChatClient.create(chatModel)
    .prompt("Can you set an alarm 10 minutes from now?")
    .tools(new DateTimeTools())
    .call()
    .content();

System.out.println(response);
```

## Overview

Tool calling lifecycle:

1. Application sends tool definitions (name, description, input schema) in the chat request.
2. Model responds with requested tool name and tool arguments.
3. Application resolves and executes the tool.
4. Application processes tool result.
5. Application sends result back to model.
6. Model generates final response using tool result.

In Spring AI, tools are represented by `ToolCallback`.

- `ChatClient` and `ChatModel` can accept tool callbacks directly.
- You can also pass tool names and resolve callbacks dynamically through `ToolCallbackResolver`.
- Tool execution lifecycle is managed by `ToolCallingManager`.

## Methods as Tools

Spring AI supports method-based tools in two ways:

- Declarative: `@Tool`
- Programmatic: `MethodToolCallback`

### Declarative Specification with @Tool

Annotate methods with `@Tool`:

```java
class DateTimeTools {

    @Tool(description = "Get the current date and time in the user's timezone")
    String getCurrentDateTime() {
        return LocalDateTime.now().atZone(LocaleContextHolder.getTimeZone().toZoneId()).toString();
    }
}
```

`@Tool` attributes:

- `name`: tool name (defaults to method name)
- `description`: tool description (strongly recommended)
- `returnDirect`: return result directly to caller
- `resultConverter`: `ToolCallResultConverter` implementation

Method and class can be static or instance and can use any visibility if accessible.

AOT note: Spring beans with `@Tool` methods are supported automatically; otherwise provide reflection metadata (for example via `@RegisterReflection`).

Method parameters and return types support many serializable types (primitives, POJOs, enums, lists, arrays, maps). Some types are unsupported (see limitations section).

Use `@ToolParam` to enrich parameter schema:

```java
class DateTimeTools {

    @Tool(description = "Set a user alarm for the given time")
    void setAlarm(@ToolParam(description = "Time in ISO-8601 format") String time) {
        LocalDateTime alarmTime = LocalDateTime.parse(time, DateTimeFormatter.ISO_DATE_TIME);
        System.out.println("Alarm set for " + alarmTime);
    }
}
```

`@ToolParam` attributes:

- `description`: parameter guidance
- `required`: required/optional flag

If parameter is annotated with `@Nullable`, it is treated as optional unless explicitly forced as required.

You can also use `@Schema` (Swagger) or `@JsonProperty` (Jackson).

### Adding Declarative Tools to ChatClient

Per request:

```java
ChatClient.create(chatModel)
    .prompt("What day is tomorrow?")
    .tools(new DateTimeTools())
    .call()
    .content();
```

Convert annotated methods explicitly:

```java
ToolCallback[] dateTimeTools = ToolCallbacks.from(new DateTimeTools());
```

Default tools on builder:

```java
ChatModel chatModel = ...;
ChatClient chatClient = ChatClient.builder(chatModel)
    .defaultTools(new DateTimeTools())
    .build();
```

Runtime tools override defaults.

### Adding Declarative Tools to ChatModel

Per request:

```java
ChatModel chatModel = ...;
ToolCallback[] dateTimeTools = ToolCallbacks.from(new DateTimeTools());
ChatOptions chatOptions = ToolCallingChatOptions.builder()
    .toolCallbacks(dateTimeTools)
    .build();
Prompt prompt = new Prompt("What day is tomorrow?", chatOptions);
chatModel.call(prompt);
```

Default tools at model creation:

```java
ToolCallback[] dateTimeTools = ToolCallbacks.from(new DateTimeTools());
ChatModel chatModel = OllamaChatModel.builder()
    .ollamaApi(OllamaApi.builder().build())
    .defaultOptions(ToolCallingChatOptions.builder()
        .toolCallbacks(dateTimeTools)
        .build())
    .build();
```

### Programmatic Specification with MethodToolCallback

```java
class DateTimeTools {
    String getCurrentDateTime() {
        return LocalDateTime.now().atZone(LocaleContextHolder.getTimeZone().toZoneId()).toString();
    }
}

Method method = ReflectionUtils.findMethod(DateTimeTools.class, "getCurrentDateTime");
ToolCallback toolCallback = MethodToolCallback.builder()
    .toolDefinition(ToolDefinitions.builder(method)
        .description("Get the current date and time in the user's timezone")
        .build())
    .toolMethod(method)
    .toolObject(new DateTimeTools())
    .build();
```

Builder concepts:

- `toolDefinition` (`ToolDefinition`): name, description, input schema
- `toolMetadata` (`ToolMetadata`): return-direct and related metadata
- `toolMethod`: `Method` to call
- `toolObject`: instance for non-static method
- `toolCallResultConverter`: custom result conversion

For static methods, `toolObject()` is optional.

### Method Tool Limitations

Unsupported method tool parameter/return types include:

- `Optional`
- Asynchronous types (`CompletableFuture`, `Future`)
- Reactive types (`Flow`, `Mono`, `Flux`)
- Functional types (`Function`, `Supplier`, `Consumer`)

For functional types, use function-based tools.

## Functions as Tools

Spring AI supports function-based tools via:

- Programmatic `FunctionToolCallback`
- Dynamic runtime resolution from Spring beans (`ToolCallbackResolver`)

### Programmatic Specification with FunctionToolCallback

```java
public class WeatherService implements Function<WeatherRequest, WeatherResponse> {
    public WeatherResponse apply(WeatherRequest request) {
        return new WeatherResponse(30.0, Unit.C);
    }
}

public enum Unit { C, F }
public record WeatherRequest(String location, Unit unit) {}
public record WeatherResponse(double temp, Unit unit) {}

ToolCallback toolCallback = FunctionToolCallback
    .builder("currentWeather", new WeatherService())
    .description("Get the weather in location")
    .inputType(WeatherRequest.class)
    .build();
```

Builder concepts:

- `name` (required)
- `toolFunction` (required): `Function`, `Supplier`, `Consumer`, or `BiFunction`
- `description`
- `inputType` (required)
- `inputSchema` (optional override)
- `toolMetadata`
- `toolCallResultConverter`

Function input/output can be `Void` or serializable POJOs. Function and involved types must be public.

### Dynamic Specification with @Bean

Expose function beans and resolve by name at runtime.

```java
@Configuration(proxyBeanMethods = false)
class WeatherTools {

    WeatherService weatherService = new WeatherService();

    @Bean
    @Description("Get the weather in location")
    Function<WeatherRequest, WeatherResponse> currentWeather() {
        return weatherService;
    }
}
```

Bean name is used as tool name. `@Description` provides tool description.

Add schema hints to input type:

```java
record WeatherRequest(
    @ToolParam(description = "The name of a city or a country") String location,
    Unit unit
) {}
```

Use constants to avoid hardcoded tool names:

```java
@Configuration(proxyBeanMethods = false)
class WeatherTools {

    public static final String CURRENT_WEATHER_TOOL = "currentWeather";

    @Bean(CURRENT_WEATHER_TOOL)
    @Description("Get the weather in location")
    Function<WeatherRequest, WeatherResponse> currentWeather() {
        return new WeatherService();
    }
}
```

### Adding Function Tools to ChatClient and ChatModel

Programmatic callback per request:

```java
ToolCallback toolCallback = ...;

ChatClient.create(chatModel)
    .prompt("What's the weather like in Copenhagen?")
    .toolCallbacks(toolCallback)
    .call()
    .content();
```

Dynamic bean name per request:

```java
ChatClient.create(chatModel)
    .prompt("What's the weather like in Copenhagen?")
    .toolNames("currentWeather")
    .call()
    .content();
```

Defaults on builder/model follow same pattern as method tools. Runtime values override defaults.

### Function Tool Limitations

Unsupported function tool input/output types include:

- Primitive types
- `Optional`
- Collections (`List`, `Map`, arrays, `Set`)
- Asynchronous types (`CompletableFuture`, `Future`)
- Reactive types (`Flow`, `Mono`, `Flux`)

For primitives and collections, prefer method-based tools.

## Tool Specification

### ToolCallback

`ToolCallback` defines tool metadata and execution contract.

```java
public interface ToolCallback {

    ToolDefinition getToolDefinition();

    ToolMetadata getToolMetadata();

    String call(String toolInput);

    String call(String toolInput, ToolContext toolContext);
}
```

### ToolDefinition

`ToolDefinition` defines tool identity and input schema.

```java
public interface ToolDefinition {

    String name();

    String description();

    String inputSchema();
}
```

Builder example:

```java
ToolDefinition toolDefinition = ToolDefinition.builder()
    .name("currentWeather")
    .description("Get the weather in location")
    .inputSchema("""
        {
            "type": "object",
            "properties": {
                "location": { "type": "string" },
                "unit": {
                    "type": "string",
                    "enum": ["C", "F"]
                }
            },
            "required": ["location", "unit"]
        }
        """)
    .build();
```

Method-derived definition:

```java
Method method = ReflectionUtils.findMethod(DateTimeTools.class, "getCurrentDateTime");
ToolDefinition toolDefinition = ToolDefinitions.from(method);
```

Customized method-derived definition:

```java
Method method = ReflectionUtils.findMethod(DateTimeTools.class, "getCurrentDateTime");
ToolDefinition toolDefinition = ToolDefinitions.builder(method)
    .name("currentDateTime")
    .description("Get the current date and time in the user's timezone")
    .inputSchema(JsonSchemaGenerator.generateForMethodInput(method))
    .build();
```

### JSON Schema

Spring AI generates tool input JSON schema using `JsonSchemaGenerator`.

Supported annotation-based customizations include:

- Descriptions:
  - `@ToolParam(description = "...")`
  - `@JsonClassDescription`
  - `@JsonPropertyDescription`
  - `@Schema(description = "...")`
- Required/optional status (precedence order):
  - `@ToolParam(required = false)`
  - `@JsonProperty(required = false)`
  - `@Schema(required = false)`
  - `@Nullable`

Description example:

```java
class DateTimeTools {

    @Tool(description = "Set a user alarm for the given time")
    void setAlarm(@ToolParam(description = "Time in ISO-8601 format") String time) {
        LocalDateTime alarmTime = LocalDateTime.parse(time, DateTimeFormatter.ISO_DATE_TIME);
        System.out.println("Alarm set for " + alarmTime);
    }
}
```

Optional parameter example:

```java
class CustomerTools {

    @Tool(description = "Update customer information")
    void updateCustomerInfo(Long id, String name, @ToolParam(required = false) String email) {
        System.out.println("Updated info for customer with id: " + id);
    }
}
```

## Result Conversion

Tool results are serialized via `ToolCallResultConverter` before being sent back to the model.

```java
@FunctionalInterface
public interface ToolCallResultConverter {

    String convert(@Nullable Object result, @Nullable Type returnType);
}
```

Default conversion uses Jackson (`DefaultToolCallResultConverter`), but custom converters are supported.

Method tool custom converter (declarative):

```java
class CustomerTools {

    @Tool(description = "Retrieve customer information", resultConverter = CustomToolCallResultConverter.class)
    Customer getCustomerInfo(Long id) {
        return customerRepository.findById(id);
    }
}
```

Programmatic method/function approaches can set custom converters via respective builders.

## Tool Context

`ToolContext` allows passing user-provided context into tool execution without exposing that context to the model.

```java
class CustomerTools {

    @Tool(description = "Retrieve customer information")
    Customer getCustomerInfo(Long id, ToolContext toolContext) {
        return customerRepository.findById(id, toolContext.getContext().get("tenantId"));
    }
}
```

`ChatClient` example:

```java
ChatModel chatModel = ...;

String response = ChatClient.create(chatModel)
    .prompt("Tell me more about the customer with ID 42")
    .tools(new CustomerTools())
    .toolContext(Map.of("tenantId", "acme"))
    .call()
    .content();

System.out.println(response);
```

`ChatModel` example:

```java
ChatModel chatModel = ...;
ToolCallback[] customerTools = ToolCallbacks.from(new CustomerTools());
ChatOptions chatOptions = ToolCallingChatOptions.builder()
    .toolCallbacks(customerTools)
    .toolContext(Map.of("tenantId", "acme"))
    .build();
Prompt prompt = new Prompt("Tell me more about the customer with ID 42", chatOptions);
chatModel.call(prompt);
```

When default and runtime tool context are both set, runtime values take precedence during merge.

## Return Direct

By default, tool results are sent back to the model to continue reasoning.

Set `returnDirect=true` for tools that should return directly to the caller.

If multiple tools are called in the same iteration, all must have `returnDirect=true` for direct return behavior.

Method tool example:

```java
class CustomerTools {

    @Tool(description = "Retrieve customer information", returnDirect = true)
    Customer getCustomerInfo(Long id) {
        return customerRepository.findById(id);
    }
}
```

Programmatic metadata example:

```java
ToolMetadata toolMetadata = ToolMetadata.builder()
    .returnDirect(true)
    .build();
```

Same metadata pattern applies to function tools.

## Tool Execution

Tool execution lifecycle is managed by `ToolCallingManager`.

```java
public interface ToolCallingManager {

    List<ToolDefinition> resolveToolDefinitions(ToolCallingChatOptions chatOptions);

    ToolExecutionResult executeToolCalls(Prompt prompt, ChatResponse chatResponse);
}
```

With Spring Boot starters, `DefaultToolCallingManager` is auto-configured.

Custom bean example:

```java
@Bean
ToolCallingManager toolCallingManager() {
    return ToolCallingManager.builder().build();
}
```

### Framework-Controlled Tool Execution

Default behavior:

1. Send prompt with tool definitions.
2. Model returns tool call request.
3. `ChatModel` delegates to `ToolCallingManager`.
4. Manager executes tool(s).
5. Tool result is returned to manager.
6. Manager returns execution result to `ChatModel`.
7. `ChatModel` sends tool result back to model.
8. Model returns final response.

Tool execution eligibility is controlled by `ToolExecutionEligibilityPredicate`.
Default predicate checks:

- `internalToolExecutionEnabled` is `true`
- chat response contains tool calls

```java
public class DefaultToolExecutionEligibilityPredicate implements ToolExecutionEligibilityPredicate {

    @Override
    public boolean test(ChatOptions promptOptions, ChatResponse chatResponse) {
        return ToolCallingChatOptions.isInternalToolExecutionEnabled(promptOptions)
            && chatResponse != null
            && chatResponse.hasToolCalls();
    }
}
```

You can provide your own predicate implementation when configuring `ChatModel`.

### Advisor-Controlled Tool Execution with ToolCallAdvisor

As an alternative, use `ToolCallAdvisor` in the advisor chain.

Benefits:

- Observability of each tool-call iteration by other advisors
- Works with chat memory advisors
- Extensible behavior

```java
var toolCallAdvisor = ToolCallAdvisor.builder()
    .toolCallingManager(toolCallingManager)
    .advisorOrder(BaseAdvisor.HIGHEST_PRECEDENCE + 300)
    .build();

var chatClient = ChatClient.builder(chatModel)
    .defaultAdvisors(toolCallAdvisor)
    .build();

String response = chatClient.prompt("What day is tomorrow?")
    .tools(new DateTimeTools())
    .call()
    .content();
```

Builder options:

- `toolCallingManager`
- `advisorOrder`
- `conversationHistoryEnabled` (default `true`)

Disable advisor-managed memory when using a dedicated chat memory advisor:

```java
var toolCallAdvisor = ToolCallAdvisor.builder()
    .toolCallingManager(toolCallingManager)
    .disableMemory()
    .advisorOrder(BaseAdvisor.HIGHEST_PRECEDENCE + 300)
    .build();

var chatMemoryAdvisor = MessageChatMemoryAdvisor.builder(chatMemory)
    .advisorOrder(BaseAdvisor.HIGHEST_PRECEDENCE + 200)
    .build();

var chatClient = ChatClient.builder(chatModel)
    .defaultAdvisors(chatMemoryAdvisor, toolCallAdvisor)
    .build();
```

`ToolCallAdvisor` also supports return-direct: if a tool call has `returnDirect=true`, it exits the loop and returns the tool result directly.
