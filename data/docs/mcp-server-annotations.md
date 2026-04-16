---
title: "MCP Server Annotations"
category: "MCP"
source: "MCP Server Annotations __ Spring AI Reference.pdf"
generated_by: "springai-kb-converter"
---

# MCP Server Annotations

Spring AI MCP Server Annotations provide a declarative way to implement MCP server functionality in Java.

They reduce boilerplate for tools, resources, prompts, and completion handlers while keeping the method model compatible with Spring Boot auto-configuration.

## Supported Annotations

### `@McpTool`

Use `@McpTool` to expose a method as an MCP tool.

```java
@Component
public class CalculatorTools {

    @McpTool(name = "add", description = "Add two numbers together")
    public int add(
            @McpToolParam(description = "First number", required = true) int a,
            @McpToolParam(description = "Second number", required = true) int b) {
        return a + b;
    }
}
```

You can also attach tool annotations that influence tool metadata:

```java
@McpTool(
        name = "calculate-area",
        description = "Calculate the area of a rectangle",
        annotations = McpTool.McpAnnotations(
                title = "Rectangle Area Calculator",
                readOnlyHint = true,
                destructiveHint = false,
                idempotentHint = true))
public AreaResult calculateRectangleArea(
        @McpToolParam(description = "Width", required = true) double width,
        @McpToolParam(description = "Height", required = true) double height) {
    return new AreaResult(width * height, "square units");
}
```

### `@McpResource`

Use `@McpResource` to expose data through URI templates.

```java
@Component
public class ResourceProvider {

    @McpResource(
            uri = "config://{key}",
            name = "Configuration",
            description = "Provides configuration data")
    public String getConfig(String key) {
        return configData.get(key);
    }
}
```

For richer responses, return `ReadResourceResult`.

```java
@McpResource(
        uri = "user-profile://{username}",
        name = "User Profile",
        description = "Provides user profile information")
public ReadResourceResult getUserProfile(String username) {
    String profileData = loadUserProfile(username);
    return new ReadResourceResult(List.of(
            new TextResourceContents("user-profile://" + username, "application/json", profileData)
    ));
}
```

### `@McpPrompt`

Use `@McpPrompt` to generate prompt messages.

```java
@Component
public class PromptProvider {

    @McpPrompt(name = "greeting", description = "Generate a greeting message")
    public GetPromptResult greeting(
            @McpArg(name = "name", description = "User's name", required = true) String name) {
        String message = "Hello, " + name + "! How can I help you today?";
        return new GetPromptResult(
                "Greeting",
                List.of(new PromptMessage(Role.ASSISTANT, new TextContent(message))));
    }
}
```

Optional prompt arguments are also supported:

```java
@McpPrompt(name = "personalized-message", description = "Generate a personalized message")
public GetPromptResult personalizedMessage(
        @McpArg(name = "name", required = true) String name,
        @McpArg(name = "age", required = false) Integer age,
        @McpArg(name = "interests", required = false) String interests) {

    StringBuilder message = new StringBuilder();
    message.append("Hello, ").append(name).append("!\n\n");

    if (age != null) {
        message.append("At ").append(age).append(" years old, ");
    }

    if (interests != null && !interests.isEmpty()) {
        message.append("Your interest in ").append(interests);
    }

    return new GetPromptResult(
            "Personalized Message",
            List.of(new PromptMessage(Role.ASSISTANT, new TextContent(message.toString()))));
}
```

### `@McpComplete`

Use `@McpComplete` to provide completion suggestions for prompt arguments.

```java
@Component
public class CompletionProvider {

    @McpComplete(prompt = "city-search")
    public List<String> completeCityName(String prefix) {
        return cities.stream()
                .filter(city -> city.toLowerCase().startsWith(prefix.toLowerCase()))
                .limit(10)
                .toList();
    }
}
```

If you need argument-aware completion, use `CompleteRequest.CompleteArgument`:

```java
@McpComplete(prompt = "travel-planner")
public List<String> completeTravelDestination(CompleteRequest.CompleteArgument argument) {
    String prefix = argument.value().toLowerCase();
    String argumentName = argument.name();

    if ("city".equals(argumentName)) {
        return completeCities(prefix);
    }
    if ("country".equals(argumentName)) {
        return completeCountries(prefix);
    }

    return List.of();
}
```

## Request Context

The preferred way to access request state is through `McpSyncRequestContext` or `McpAsyncRequestContext`.

These contexts provide logging, progress, sampling, elicitation, request metadata, and transport access where supported.

```java
public record UserInfo(String name, String email, int age) {}

@McpTool(name = "unified-tool", description = "Tool with unified request context")
public String unifiedTool(
        McpSyncRequestContext context,
        @McpToolParam(description = "Input", required = true) String input) {

    context.info("Processing: " + input);
    context.progress(50);
    context.ping();

    if (context.elicitEnabled()) {
        StructuredElicitResult<UserInfo> elicitResult = context.elicit(UserInfo.class);
        if (elicitResult.action() == ElicitResult.Action.ACCEPT) {
            // Use elicited data
        }
    }

    if (context.sampleEnabled()) {
        CreateMessageResult samplingResult = context.sample("Generate response");
        // Use sampling result
    }

    return "Processed with unified context";
}
```

For simple operations, you can omit context parameters entirely.

For stateless operations, use `McpTransportContext` when you only need lightweight transport access.

```java
@McpTool(name = "stateless-tool", description = "Stateless with transport context")
public String statelessTool(
        McpTransportContext context,
        @McpToolParam(description = "Input", required = true) String input) {
    return "Processed: " + input;
}
```

Stateless servers do not support bidirectional operations such as roots, elicitation, or sampling.

## Server Type Filtering

The framework filters annotated methods based on the configured server type.

### Sync Servers

Sync servers accept non-reactive return types such as primitives, objects, collections, and MCP result types.

They filter out reactive methods such as `Mono<T>`, `Flux<T>`, and `Publisher<T>`.

```java
@Component
public class SyncTools {

    @McpTool(name = "sync-tool", description = "Synchronous tool")
    public String syncTool(String input) {
        return "Processed: " + input;
    }

    @McpTool(name = "async-tool", description = "Async tool")
    public Mono<String> asyncTool(String input) {
        return Mono.just("Processed: " + input);
    }
}
```

### Async Servers

Async servers accept reactive return types such as `Mono<T>`, `Flux<T>`, and `Publisher<T>`.

They filter out non-reactive methods.

```java
@Component
public class AsyncTools {

    @McpTool(name = "async-tool", description = "Async tool")
    public Mono<String> asyncTool(String input) {
        return Mono.just("Processed: " + input);
    }

    @McpTool(name = "sync-tool", description = "Sync tool")
    public String syncTool(String input) {
        return "Processed: " + input;
    }
}
```

### Stateful vs Stateless Filtering

Stateful servers support bidirectional communication and allow request contexts that can trigger roots, elicitation, and sampling.

Stateless servers only support lightweight request handling and filter out methods that depend on bidirectional context.

Use `McpSyncRequestContext` or `McpAsyncRequestContext` for stateful deployments, and `McpTransportContext` for stateless deployments.

## Async Support

Server annotations also support reactive implementations.

```java
@Component
public class AsyncTools {

    @McpTool(name = "async-fetch", description = "Fetch data asynchronously")
    public Mono<String> asyncFetch(
            @McpToolParam(description = "URL", required = true) String url) {
        return Mono.fromCallable(() -> fetchFromUrl(url))
                .subscribeOn(Schedulers.boundedElastic());
    }

    @McpResource(uri = "async-data://{id}", name = "Async Data")
    public Mono<ReadResourceResult> asyncResource(String id) {
        return Mono.fromCallable(() -> {
            String data = loadData(id);
            return new ReadResourceResult(List.of(
                    new TextResourceContents("async-data://" + id, "text/plain", data)
            ));
        });
    }
}
```

## Spring Boot Integration

With Spring Boot auto-configuration, annotated beans are detected and registered automatically.

```java
@SpringBootApplication
public class McpServerApplication {
    public static void main(String[] args) {
        SpringApplication.run(McpServerApplication.class, args);
    }
}

@Component
public class MyMcpTools {
    // Your @McpTool annotated methods
}

@Component
public class MyMcpResources {
    // Your @McpResource annotated methods
}
```

The auto-configuration will:

1. Scan for beans with MCP annotations.
2. Create appropriate specifications.
3. Register them with the MCP server.
4. Handle sync and async implementations based on configuration.

## Configuration

Enable the server annotation scanner and set the server type in application properties:

```yaml
spring:
  ai:
    mcp:
      server:
        type: SYNC
        annotation-scanner:
          enabled: true
```

## Notes

- Use `@McpTool` for executable server operations.
- Use `@McpResource` for URI-based data access.
- Use `@McpPrompt` for reusable prompt generation.
- Use `@McpComplete` for prompt completion suggestions.
- Use request contexts when you need logging, progress, sampling, or elicitation.
- Keep sync and async handler methods aligned with the configured server type.
