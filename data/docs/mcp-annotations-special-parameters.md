---
title: "MCP Annotations Special Parameters"
category: "MCP"
source: "MCP Annotations Special Parameters __ Spring AI Reference.pdf"
generated_by: "springai-kb-converter"
---

# MCP Annotations Special Parameters

Spring AI MCP annotations support special parameter types that give annotated methods access to request metadata, progress reporting, the full request, and request-scoped server context.

These parameters are injected by the framework and are excluded from JSON schema generation.

## Special Parameter Types

### `McpMeta`

`McpMeta` provides access to metadata from MCP requests, notifications, and results.

It is useful when a tool, resource, or prompt needs to adapt its behavior based on request metadata.

```java
@McpTool(name = "contextual-tool", description = "Tool with metadata access")
public String processWithContext(
        @McpToolParam(description = "Input data", required = true) String data,
        McpMeta meta) {

    String userId = (String) meta.get("userId");
    String userRole = (String) meta.get("userRole");

    if ("admin".equals(userRole)) {
        return processAsAdmin(data, userId);
    }

    return processAsUser(data, userId);
}
```

### `@McpProgressToken`

`@McpProgressToken` marks a `String` parameter that receives the request progress token, if one is present.

Use it when you need to emit progress notifications for long-running operations.

```java
@McpTool(name = "long-operation", description = "Long-running operation with progress")
public String performLongOperation(
        @McpProgressToken String progressToken,
        @McpToolParam(description = "Operation name", required = true) String operation,
        @McpToolParam(description = "Duration in seconds", required = true) int duration,
        McpSyncServerExchange exchange) throws InterruptedException {

    if (progressToken != null) {
        exchange.progressNotification(new ProgressNotification(progressToken, 0.0, 1.0, "Starting " + operation));
    }

    for (int i = 1; i <= duration; i++) {
        Thread.sleep(1000);
        if (progressToken != null) {
            double progress = (double) i / duration;
            exchange.progressNotification(new ProgressNotification(
                    progressToken,
                    progress,
                    1.0,
                    "Processing... " + (int) (progress * 100) + "%"));
        }
    }

    return "Operation " + operation + " completed";
}
```

### `McpSyncRequestContext` and `McpAsyncRequestContext`

Request context objects provide a unified interface for accessing MCP request information and server-side operations.

They are useful when you need logging, progress updates, elicitation, sampling, or direct access to the request.

```java
public record UserInfo(String name, String email, int age) {}

@McpTool(name = "advanced-tool", description = "Tool with full server capabilities")
public String advancedTool(
        McpSyncRequestContext context,
        @McpToolParam(description = "Input", required = true) String input) {

    context.info("Processing: " + input);
    context.ping();
    context.progress(50);

    if (context.elicitEnabled()) {
        StructuredElicitResult<UserInfo> elicitResult = context.elicit(
                e -> e.message("Need additional information"),
                UserInfo.class);

        if (elicitResult.action() == ElicitResult.Action.ACCEPT) {
            UserInfo userInfo = elicitResult.structuredContent();
            return "Processed for " + userInfo.name();
        }
    }

    if (context.sampleEnabled()) {
        CreateMessageResult samplingResult = context.sample(
                s -> s.message("Process: " + input)
                        .modelPreferences(pref -> pref.modelHints("gpt-4")));
    }

    return "Processed with advanced features";
}
```

The asynchronous version exposes the same capabilities with reactive return types:

```java
public record UserInfo(String name, String email, int age) {}

@McpTool(name = "async-advanced-tool", description = "Async tool with server capabilities")
public Mono<String> asyncAdvancedTool(
        McpAsyncRequestContext context,
        @McpToolParam(description = "Input", required = true) String input) {

    return context.info("Async processing: " + input)
            .then(context.progress(25))
            .then(context.ping())
            .then(Mono.defer(() -> {
                if (context.elicitEnabled()) {
                    return context.elicitation(UserInfo.class)
                            .map(userInfo -> "Processing for user: " + userInfo.name());
                }
                return Mono.just("Processing...");
            }))
            .flatMap(msg -> {
                if (context.sampleEnabled()) {
                    return context.sampling("Process: " + input)
                            .map(result -> "Completed: " + result);
                }
                return Mono.just("Completed: " + msg);
            });
}
```

### `McpTransportContext`

`McpTransportContext` is a lightweight context for stateless operations.

It provides limited access to transport-level details without the full server exchange API.

```java
@McpTool(name = "stateless-tool", description = "Stateless tool with context")
public String statelessTool(
        McpTransportContext context,
        @McpToolParam(description = "Input", required = true) String input) {

    return "Processed in stateless mode: " + input;
}
```

```java
@McpResource(uri = "stateless://{id}", name = "Stateless Resource")
public ReadResourceResult statelessResource(
        McpTransportContext context,
        String id) {

    String data = loadData(id);
    return new ReadResourceResult(List.of(
            new TextResourceContents("stateless://" + id, "text/plain", data)
    ));
}
```

### `CallToolRequest`

`CallToolRequest` gives a tool access to the full request payload, which is useful for dynamic schemas and flexible argument handling.

```java
@McpTool(name = "dynamic-tool", description = "Tool with dynamic schema support")
public CallToolResult processDynamicSchema(CallToolRequest request) {
    Map<String, Object> args = request.arguments();

    StringBuilder result = new StringBuilder("Processed:\n");
    for (Map.Entry<String, Object> entry : args.entrySet()) {
        result.append("  ").append(entry.getKey())
                .append(": ").append(entry.getValue())
                .append("\n");
    }

    return CallToolResult.builder()
            .addTextContent(result.toString())
            .build();
}
```

You can also combine typed parameters with the raw request:

```java
@McpTool(name = "hybrid-tool", description = "Tool with typed and dynamic parameters")
public String processHybrid(
        @McpToolParam(description = "Operation", required = true) String operation,
        @McpToolParam(description = "Priority", required = false) Integer priority,
        CallToolRequest request) {

    String result = "Operation: " + operation;
    if (priority != null) {
        result += " (Priority: " + priority + ")";
    }

    Map<String, Object> allArgs = request.arguments();
    Map<String, Object> additionalArgs = new HashMap<>(allArgs);
    additionalArgs.remove("operation");
    additionalArgs.remove("priority");

    if (!additionalArgs.isEmpty()) {
        result += " with " + additionalArgs.size() + " additional parameters";
    }

    return result;
}
```

## Parameter Injection Rules

### Automatic Injection

The framework automatically injects these parameter types when they appear in a supported MCP method:

- `McpMeta`
- `@McpProgressToken String`
- `McpSyncRequestContext` and `McpAsyncRequestContext`
- `McpTransportContext`
- `CallToolRequest`

### Schema Generation

Special parameters are excluded from generated JSON schema.

That means they do not appear in the tool input schema, they do not count against parameter limits, and they are hidden from MCP clients.

### Null Handling

- `McpMeta` is never `null`; an empty instance is injected when no metadata is present.
- `@McpProgressToken` can be `null` when no progress token is supplied.
- `McpSyncRequestContext` and `McpAsyncRequestContext` are injected when supported by the method signature.
- `CallToolRequest` is available for tool methods that need the raw request.

## Best Practices

Use `McpMeta` when behavior depends on request metadata such as user identity, access level, or locale.

Check progress tokens for `null` before emitting progress notifications.

Prefer request context objects when you need multiple capabilities at once, such as logging plus progress plus elicitation.

Use `CallToolRequest` only when the tool needs access to dynamic or unknown arguments at runtime.
