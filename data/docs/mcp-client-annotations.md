---
title: "MCP Client Annotations"
category: "MCP"
source: "MCP Client Annotations __ Spring AI Reference.pdf"
generated_by: "springai-kb-converter"
---

# MCP Client Annotations

Spring AI MCP Client Annotations provide a declarative way to implement MCP client-side handlers in Java.

Each annotated handler is associated with one or more MCP client connections using the `clients` attribute. The value must match a connection name configured in your application properties.

## Supported Annotations

### `@McpLogging`

Use `@McpLogging` to handle logging notifications sent by an MCP server.

```java
@Component
public class LoggingHandler {

    @McpLogging(clients = "my-mcp-server")
    public void handleLoggingMessage(LoggingMessageNotification notification) {
        System.out.println("Received log: " + notification.level() + " - " + notification.data());
    }
}
```

You can also bind the individual logging fields directly when that is more convenient:

```java
@McpLogging(clients = "my-mcp-server")
public void handleLoggingWithParams(LoggingLevel level, String logger, String data) {
    System.out.println(String.format("[%s] %s: %s", level, logger, data));
}
```

### `@McpSampling`

Use `@McpSampling` to respond to sampling requests from a server.

```java
@Component
public class SamplingHandler {

    @McpSampling(clients = "llm-server")
    public CreateMessageResult handleSamplingRequest(CreateMessageRequest request) {
        String response = generateLLMResponse(request);

        return CreateMessageResult.builder()
                .role(Role.ASSISTANT)
                .content(new TextContent(response))
                .model("gpt-4")
                .build();
    }
}
```

Reactive handlers are also supported:

```java
@Component
public class AsyncSamplingHandler {

    @McpSampling(clients = "llm-server")
    public Mono<CreateMessageResult> handleAsyncSampling(CreateMessageRequest request) {
        return Mono.fromCallable(() -> {
            String response = generateLLMResponse(request);
            return CreateMessageResult.builder()
                    .role(Role.ASSISTANT)
                    .content(new TextContent(response))
                    .model("gpt-4")
                    .build();
        }).subscribeOn(Schedulers.boundedElastic());
    }
}
```

### `@McpElicitation`

Use `@McpElicitation` when the server needs to gather additional information from a user.

```java
@Component
public class ElicitationHandler {

    @McpElicitation(clients = "interactive-server")
    public ElicitResult handleElicitationRequest(ElicitRequest request) {
        Map<String, Object> userData = presentFormToUser(request.requestedSchema());

        if (userData != null) {
            return new ElicitResult(ElicitResult.Action.ACCEPT, userData);
        }

        return new ElicitResult(ElicitResult.Action.DECLINE, null);
    }
}
```

When the schema is more detailed, you can inspect it and collect values field by field:

```java
@McpElicitation(clients = "interactive-server")
public ElicitResult handleInteractiveElicitation(ElicitRequest request) {
    Map<String, Object> schema = request.requestedSchema();
    Map<String, Object> userData = new HashMap<>();

    if (schema != null && schema.containsKey("properties")) {
        Map<String, Object> properties = (Map<String, Object>) schema.get("properties");

        if (properties.containsKey("name")) {
            userData.put("name", promptUser("Enter your name:"));
        }
        if (properties.containsKey("email")) {
            userData.put("email", promptUser("Enter your email:"));
        }
        if (properties.containsKey("preferences")) {
            userData.put("preferences", gatherPreferences());
        }
    }

    return new ElicitResult(ElicitResult.Action.ACCEPT, userData);
}
```

### `@McpProgress`

Use `@McpProgress` to receive progress notifications for long-running operations.

```java
@Component
public class ProgressHandler {

    @McpProgress(clients = "my-mcp-server")
    public void handleProgressNotification(ProgressNotification notification) {
        double percentage = notification.progress() * 100;
        System.out.println(String.format("Progress: %.2f%% - %s", percentage, notification.message()));
    }
}
```

### `@McpToolListChanged`

Use `@McpToolListChanged` when the remote server’s tool list changes.

```java
@Component
public class ToolListChangedHandler {

    @McpToolListChanged(clients = "tool-server")
    public void handleToolListChanged(List<McpSchema.Tool> updatedTools) {
        System.out.println("Tool list updated: " + updatedTools.size() + " tools available");
        toolRegistry.updateTools(updatedTools);

        for (McpSchema.Tool tool : updatedTools) {
            System.out.println("  - " + tool.name() + ": " + tool.description());
        }
    }
}
```

### `@McpResourceListChanged`

Use `@McpResourceListChanged` when the remote server’s resource list changes.

```java
@Component
public class ResourceListChangedHandler {

    @McpResourceListChanged(clients = "resource-server")
    public void handleResourceListChanged(List<McpSchema.Resource> updatedResources) {
        System.out.println("Resources updated: " + updatedResources.size());
        resourceCache.clear();
        for (McpSchema.Resource resource : updatedResources) {
            resourceCache.register(resource);
        }
    }
}
```

### `@McpPromptListChanged`

Use `@McpPromptListChanged` when the server’s prompt list changes.

```java
@Component
public class PromptListChangedHandler {

    @McpPromptListChanged(clients = "prompt-server")
    public void handlePromptListChanged(List<McpSchema.Prompt> updatedPrompts) {
        System.out.println("Prompts updated: " + updatedPrompts.size());
        promptCatalog.updatePrompts(updatedPrompts);

        if (uiController != null) {
            uiController.refreshPromptList(updatedPrompts);
        }
    }
}
```

## Spring Boot Integration

With Spring Boot auto-configuration, annotated client handler beans are discovered and registered automatically.

```java
@SpringBootApplication
public class McpClientApplication {
    public static void main(String[] args) {
        SpringApplication.run(McpClientApplication.class, args);
    }
}

@Component
public class MyClientHandlers {

    @McpLogging(clients = "my-server")
    public void handleLogs(LoggingMessageNotification notification) {
        // Handle logs
    }

    @McpSampling(clients = "my-server")
    public CreateMessageResult handleSampling(CreateMessageRequest request) {
        // Handle sampling
    }

    @McpProgress(clients = "my-server")
    public void handleProgress(ProgressNotification notification) {
        // Handle progress
    }
}
```

Spring Boot will:

1. Scan for beans with MCP client annotations.
2. Create the appropriate client handler registrations.
3. Match handlers to the configured `clients` names.
4. Support both synchronous and reactive handler methods.
5. Allow multiple client connections with separate handlers.

## Configuration

Configure client annotation scanning and client connections with application properties:

```yaml
spring:
  ai:
    mcp:
      client:
        type: SYNC
        annotation-scanner:
          enabled: true
        sse:
          connections:
            my-server:
              url: http://localhost:8080
            tool-server:
              url: http://localhost:8081
        stdio:
          connections:
            local-server:
              command: /path/to/mcp-server
              args:
                - --mode=production
```

The `clients` values in annotations must match the configured connection names, such as `my-server`, `tool-server`, or `local-server`.

## Usage Notes

Use the typed notification objects when you want structured access to payload fields. Use individual parameters when you only need a few values and want a smaller method signature.

Reactive return types such as `Mono<Void>` and `Mono<CreateMessageResult>` are supported where the framework and handler contract allow them.

For the general annotation model, see [MCP Annotations](mcp-annotations.md). For special request context types, see [MCP Annotations Special Parameters](mcp-annotations-special-parameters.md).
