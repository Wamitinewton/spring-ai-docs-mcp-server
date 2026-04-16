---
title: "Streamable-HTTP"
category: "Streaming"
source: "Streamable-HTTP __ Spring AI Reference.pdf"
generated_by: "springai-kb-converter"
---

# Streamable-HTTP

## Streamable-HTTP MCP Servers

The Streamable-HTTP transport allows MCP servers to run as independent processes that can handle multiple client connections through HTTP `POST` and `GET` requests, with optional Server-Sent Events (SSE) streaming for server messages.
It replaces the legacy SSE transport.

These servers, introduced with spec version `2025-03-26`, are ideal for applications that need to notify clients about dynamic changes to tools, resources, or prompts.

Set `spring.ai.mcp.server.protocol=STREAMABLE`.

Use Streamable-HTTP clients to connect to Streamable-HTTP servers.

### Streamable-HTTP WebMVC Server

Use the `spring-ai-starter-mcp-server-webmvc` dependency:

```xml
<dependency>
    <groupId>org.springframework.ai</groupId>
    <artifactId>spring-ai-starter-mcp-server-webmvc</artifactId>
</dependency>
```

Set `spring.ai.mcp.server.protocol=STREAMABLE`.

- Full MCP server capabilities with Spring MVC Streamable transport
- Support for tools, resources, prompts, completion, logging, progress, ping, and root-change capabilities
- Persistent connection management

### Streamable-HTTP WebFlux Server

Use the `spring-ai-starter-mcp-server-webflux` dependency:

```xml
<dependency>
    <groupId>org.springframework.ai</groupId>
    <artifactId>spring-ai-starter-mcp-server-webflux</artifactId>
</dependency>
```

Set `spring.ai.mcp.server.protocol=STREAMABLE`.

- Reactive MCP server with WebFlux Streamable transport
- Support for tools, resources, prompts, completion, logging, progress, ping, and root-change capabilities
- Non-blocking, persistent connection management

## Configuration Properties

### Common Properties

All common properties are prefixed with `spring.ai.mcp.server`.

| Property | Description | Default |
| --- | --- | --- |
| `enabled` | Enable/disable the streamable MCP server | `true` |
| `protocol` | MCP server protocol. Must be set to `STREAMABLE` to enable streamable mode | - |
| `tool-callback-converter` | Enable/disable conversion of Spring AI `ToolCallback` instances into MCP tool specs | `true` |
| `name` | Server name for identification | `mcp-server` |
| `version` | Server version | `1.0.0` |
| `instructions` | Optional instructions for client interaction | `null` |
| `type` | Server type (`SYNC`/`ASYNC`) | `SYNC` |
| `capabilities.resource` | Enable/disable resource capabilities | `true` |
| `capabilities.tool` | Enable/disable tool capabilities | `true` |
| `capabilities.prompt` | Enable/disable prompt capabilities | `true` |
| `capabilities.completion` | Enable/disable completion capabilities | `true` |
| `resource-change-notification` | Enable resource change notifications | `true` |
| `prompt-change-notification` | Enable prompt change notifications | `true` |
| `tool-change-notification` | Enable tool change notifications | `true` |
| `tool-response-mime-type` | Response MIME type per tool name | `-` |
| `request-timeout` | Request timeout duration | `20 seconds` |

### MCP Annotations Properties

MCP Server Annotations provide a declarative way to implement MCP server handlers using Java annotations.

The annotation scanner properties are prefixed with `spring.ai.mcp.server.annotation-scanner`.

| Property | Description | Default |
| --- | --- | --- |
| `enabled` | Enable/disable MCP server annotations auto-scanning | `true` |

### Streamable-HTTP Properties

All streamable-HTTP properties are prefixed with `spring.ai.mcp.server.streamable-http`.

| Property | Description | Default |
| --- | --- | --- |
| `mcp-endpoint` | Custom MCP endpoint path | `/mcp` |
| `keep-alive-interval` | Connection keep-alive interval | `null` (disabled) |
| `disallow-delete` | Disallow delete operations | `false` |

## Features and Capabilities

The MCP Server supports four main capability types that can be individually enabled or disabled:

- Tools: `spring.ai.mcp.server.capabilities.tool=true|false`
- Resources: `spring.ai.mcp.server.capabilities.resource=true|false`
- Prompts: `spring.ai.mcp.server.capabilities.prompt=true|false`
- Completions: `spring.ai.mcp.server.capabilities.completion=true|false`

All capabilities are enabled by default. Disabling a capability prevents the server from registering and exposing the corresponding features to clients.

The MCP Server Boot Starter allows servers to expose tools, resources, prompts, and completions to clients. It automatically converts custom capability handlers registered as Spring beans into sync/async specifications based on server type.

### Tools

Allows servers to expose tools that can be invoked by language models.

- Change notification support
- Spring AI tools automatically converted to sync/async specifications based on server type
- Automatic tool specification through Spring beans

```java
@Bean
public ToolCallbackProvider myTools(...) {
    List<ToolCallback> tools = ...;
    return ToolCallbackProvider.from(tools);
}
```

Or using the low-level API:

```java
@Bean
public List<McpServerFeatures.SyncToolSpecification> myTools(...) {
    List<McpServerFeatures.SyncToolSpecification> tools = ...;
    return tools;
}
```

The auto-configuration automatically detects and registers tool callbacks from:

- Individual `ToolCallback` beans
- Lists of `ToolCallback` beans
- `ToolCallbackProvider` beans

Tools are de-duplicated by name, with the first occurrence of each tool name used.

You can disable automatic detection and registration of tool callbacks by setting `tool-callback-converter=false`.

#### Tool Context Support

`ToolContext` is supported, allowing contextual information to be passed to tool calls.
It contains an `McpSyncServerExchange` instance under the `exchange` key, accessible via `McpToolUtils.getMcpExchange(toolContext)`.

### Resources

Provides a standardized way for servers to expose resources to clients.

- Static and dynamic resource specifications
- Optional change notifications
- Support for resource templates
- Automatic conversion between sync/async resource specifications
- Automatic resource specification through Spring beans

```java
@Bean
public List<McpServerFeatures.SyncResourceSpecification> myResources(...) {
    var systemInfoResource = new McpSchema.Resource(...);
    var resourceSpecification = new McpServerFeatures.SyncResourceSpecification(systemInfoResource, (exchange, request) -> {
        try {
            var systemInfo = Map.of(...);
            String jsonContent = new ObjectMapper().writeValueAsString(systemInfo);
            return new McpSchema.ReadResourceResult(
                List.of(new McpSchema.TextResourceContents(request.uri(), "application/json", jsonContent))
            );
        }
        catch (Exception e) {
            throw new RuntimeException("Failed to generate system info", e);
        }
    });

    return List.of(resourceSpecification);
}
```

### Prompts

Provides a standardized way for servers to expose prompt templates to clients.

- Change notification support
- Template versioning
- Automatic conversion between sync/async prompt specifications
- Automatic prompt specification through Spring beans

```java
@Bean
public List<McpServerFeatures.SyncPromptSpecification> myPrompts() {
    var prompt = new McpSchema.Prompt(
        "greeting",
        "A friendly greeting prompt",
        List.of(new McpSchema.PromptArgument("name", "The name to greet", true))
    );

    var promptSpecification = new McpServerFeatures.SyncPromptSpecification(prompt, (exchange, getPromptRequest) -> {
        String nameArgument = (String) getPromptRequest.arguments().get("name");
        if (nameArgument == null) {
            nameArgument = "friend";
        }

        var userMessage = new PromptMessage(
            Role.USER,
            new TextContent("Hello " + nameArgument + "! How can I assist you today?")
        );

        return new GetPromptResult("A personalized greeting message", List.of(userMessage));
    });

    return List.of(promptSpecification);
}
```

### Completions

Provides a standardized way for servers to expose completion capabilities to clients.

- Support for both sync and async completion specifications
- Automatic registration through Spring beans

```java
@Bean
public List<McpServerFeatures.SyncCompletionSpecification> myCompletions() {
    var completion = new McpServerFeatures.SyncCompletionSpecification(
        new McpSchema.PromptReference(
            "ref/prompt",
            "code-completion",
            "Provides code completion suggestions"
        ),
        (exchange, request) -> {
            // Implementation that returns completion suggestions
            return new McpSchema.CompleteResult(List.of("python", "pytorch", "pyside"), 10, true);
        }
    );

    return List.of(completion);
}
```

### Logging

Provides a standardized way for servers to send structured log messages to clients.
From within tool, resource, prompt, or completion handlers, use the `exchange` object (`McpSyncServerExchange` / `McpAsyncServerExchange`) to send logging messages:

```java
(exchange, request) -> {
    exchange.loggingNotification(LoggingMessageNotification.builder()
        .level(LoggingLevel.INFO)
        .logger("test-logger")
        .data("This is a test log message")
        .build());
}
```

On the MCP client, register logging consumers to handle these messages:

```java
mcpClientSpec.loggingConsumer((McpSchema.LoggingMessageNotification log) -> {
    // Handle log messages
});
```

### Progress

Provides a standardized way for servers to send progress updates to clients.
From within tool, resource, prompt, or completion handlers, use the `exchange` object to send progress notifications:

```java
(exchange, request) -> {
    exchange.progressNotification(ProgressNotification.builder()
        .progressToken("test-progress-token")
        .progress(0.25)
        .total(1.0)
        .message("tool call in progress")
        .build());
}
```

The MCP client can receive progress notifications and update its UI accordingly by registering a progress consumer.

```java
mcpClientSpec.progressConsumer((McpSchema.ProgressNotification progress) -> {
    // Handle progress notifications
});
```

### Root List Changes

When roots change, clients that support `listChanged` send root-change notifications.

- Support for monitoring root changes
- Automatic conversion to async consumers for reactive applications
- Optional registration through Spring beans

```java
@Bean
public BiConsumer<McpSyncServerExchange, List<McpSchema.Root>> rootsChangeHandler() {
    return (exchange, roots) -> {
        logger.info("Registering root resources: {}", roots);
    };
}
```

### Ping

Ping mechanism for the server to verify that clients are still alive.
From within tool, resource, prompt, or completion handlers:

```java
(exchange, request) -> {
    exchange.ping();
}
```

### Keep Alive

The server can optionally issue periodic pings to connected clients to verify connection health.

By default, keep-alive is disabled. To enable it, set `keep-alive-interval` in your configuration:

```yaml
spring:
  ai:
    mcp:
      server:
        streamable-http:
          keep-alive-interval: 30s
```

For Streamable-HTTP servers, keep-alive is currently available only for the server-to-client SSE connection.

## Usage Examples

### Streamable HTTP Server Configuration

```yaml
# Using spring-ai-starter-mcp-server-streamable-webmvc
spring:
  ai:
    mcp:
      server:
        protocol: STREAMABLE
        name: streamable-mcp-server
        version: 1.0.0
        type: SYNC
        instructions: "This streamable server provides real-time notifications"
        resource-change-notification: true
        tool-change-notification: true
        prompt-change-notification: true
        streamable-http:
          mcp-endpoint: /api/mcp
          keep-alive-interval: 30s
```

### Creating a Spring Boot Application with MCP Server

```java
@Service
public class WeatherService {

    @Tool(description = "Get weather information by city name")
    public String getWeather(String cityName) {
        // Implementation
    }
}

@SpringBootApplication
public class McpServerApplication {

    private static final Logger logger = LoggerFactory.getLogger(McpServerApplication.class);

    public static void main(String[] args) {
        SpringApplication.run(McpServerApplication.class, args);
    }

    @Bean
    public ToolCallbackProvider weatherTools(WeatherService weatherService) {
        return MethodToolCallbackProvider.builder()
            .toolObjects(weatherService)
            .build();
    }
}
```

The auto-configuration automatically registers tool callbacks as MCP tools.
You can have multiple beans producing `ToolCallback` instances, and the auto-configuration merges them.
