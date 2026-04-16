---
title: "SSE-MCP"
category: "MCP"
source: "SSE-MCP __ Spring AI Reference.pdf"
generated_by: "springai-kb-converter"
---

# SSE-MCP

## STDIO and SSE MCP Servers

The STDIO and SSE MCP Server starters support multiple transport mechanisms.
Use STDIO or SSE clients to connect to the corresponding server transport.

### STDIO MCP Server

Full MCP server feature support with `STDIO` transport.

```xml
<dependency>
    <groupId>org.springframework.ai</groupId>
    <artifactId>spring-ai-starter-mcp-server</artifactId>
</dependency>
```

- Suitable for command-line and desktop tools
- No additional web dependencies required
- Configuration of basic server components
- Handling of tool, resource, and prompt specifications
- Management of server capabilities and change notifications
- Support for both sync and async server implementations

### SSE WebMVC Server

Full MCP server feature support with `SSE` (Server-Sent Events) transport based on Spring MVC, with optional `STDIO` transport.

```xml
<dependency>
    <groupId>org.springframework.ai</groupId>
    <artifactId>spring-ai-starter-mcp-server-webmvc</artifactId>
</dependency>
```

- HTTP-based transport using Spring MVC (`WebMvcSseServerTransportProvider`)
- Automatically configured SSE endpoints
- Optional `STDIO` transport (set `spring.ai.mcp.server.stdio=true`)
- Includes `spring-boot-starter-web` and `mcp-spring-webmvc` dependencies

### SSE WebFlux Server

Full MCP server feature support with `SSE` (Server-Sent Events) transport based on Spring WebFlux, with optional `STDIO` transport.

```xml
<dependency>
    <groupId>org.springframework.ai</groupId>
    <artifactId>spring-ai-starter-mcp-server-webflux</artifactId>
</dependency>
```

This starter activates `McpWebFluxServerAutoConfiguration` and `McpServerAutoConfiguration` to provide:

- Reactive transport using Spring WebFlux (`WebFluxSseServerTransportProvider`)
- Automatically configured reactive SSE endpoints
- Optional `STDIO` transport (set `spring.ai.mcp.server.stdio=true`)
- Includes `spring-boot-starter-webflux` and `mcp-spring-webflux` dependencies

When both `org.springframework.web.servlet.DispatcherServlet` and `org.springframework.web.reactive.DispatcherHandler` are on the classpath, Spring Boot prioritizes `DispatcherServlet`. If your project uses `spring-boot-starter-web`, prefer `spring-ai-starter-mcp-server-webmvc`.

## Configuration Properties

### Common Properties

All common properties are prefixed with `spring.ai.mcp.server`.

| Property | Description | Default |
| --- | --- | --- |
| `enabled` | Enable/disable the MCP server | `true` |
| `tool-callback-converter` | Enable/disable conversion of Spring AI `ToolCallback` instances into MCP tool specs | `true` |
| `stdio` | Enable/disable STDIO transport | `false` |
| `name` | Server name for identification | `mcp-server` |
| `version` | Server version | `1.0.0` |
| `instructions` | Optional instructions for clients on how to interact with this server | `null` |
| `type` | Server type (`SYNC`/`ASYNC`) | `SYNC` |
| `capabilities.resource` | Enable/disable resource capabilities | `true` |
| `capabilities.tool` | Enable/disable tool capabilities | `true` |
| `capabilities.prompt` | Enable/disable prompt capabilities | `true` |
| `capabilities.completion` | Enable/disable completion capabilities | `true` |
| `resource-change-notification` | Enable resource change notifications | `true` |
| `prompt-change-notification` | Enable prompt change notifications | `true` |
| `tool-change-notification` | Enable tool change notifications | `true` |
| `tool-response-mime-type` | Optional response MIME type per tool name. Example: `spring.ai.mcp.server.tool-response-mime-type.generateImage=image/png` | `-` |
| `request-timeout` | Duration to wait for server responses before timing out requests | `20 seconds` |

### MCP Annotations Properties

MCP Server Annotations provide a declarative way to implement MCP server handlers using Java annotations.

The annotation scanner properties are prefixed with `spring.ai.mcp.server.annotation-scanner`.

| Property | Description | Default |
| --- | --- | --- |
| `enabled` | Enable/disable MCP server annotation auto-scanning | `true` |

### SSE Properties

All SSE properties are prefixed with `spring.ai.mcp.server`.

| Property | Description | Default |
| --- | --- | --- |
| `sse-message-endpoint` | SSE message endpoint path used by clients to send messages | `/mcp/message` |
| `sse-endpoint` | SSE endpoint path for web transport | `/sse` |
| `base-url` | Optional URL prefix. Example: with `base-url=/api/v1`, effective endpoints are `/api/v1` + SSE endpoints | `-` |
| `keep-alive-interval` | Connection keep-alive interval | `null` (disabled) |

For backward compatibility, these SSE properties do not use an additional suffix (such as `.sse`).

## Features and Capabilities

The MCP Server Boot Starter allows servers to expose tools, resources, prompts, and completions to clients.
Custom capability handlers registered as Spring beans are automatically converted to sync/async specifications based on server type.

### Tools

Allows servers to expose tools that language models can invoke.

- Change notification support
- Spring AI tools are automatically converted to sync/async specifications based on server type
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

Tools are de-duplicated by name, with the first occurrence used.

Disable automatic tool callback detection by setting `tool-callback-converter=false`.

#### Tool Context Support

Tool context is supported and can pass contextual information to tool calls.
It contains an `McpSyncServerExchange` under the `exchange` key, accessible via `McpToolUtils.getMcpExchange(toolContext)`.

### Resources

Provides a standardized way for servers to expose resources to clients.

- Static and dynamic resource specifications
- Optional change notifications
- Support for resource templates
- Automatic conversion between sync/async resource specifications

Automatic resource specification through Spring beans:

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

Automatic prompt specification through Spring beans:

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
Inside tool, resource, prompt, or completion handlers, use `McpSyncServerExchange` or `McpAsyncServerExchange` to send logging notifications:

```java
(exchange, request) -> {
    exchange.loggingNotification(LoggingMessageNotification.builder()
        .level(LoggingLevel.INFO)
        .logger("test-logger")
        .data("This is a test log message")
        .build());
}
```

On the MCP client, register logging consumers to handle messages:

```java
mcpClientSpec.loggingConsumer((McpSchema.LoggingMessageNotification log) -> {
    // Handle log messages
});
```

### Progress

Provides a standardized way for servers to send progress updates to clients.
Inside tool, resource, prompt, or completion handlers, use the exchange object to send progress notifications:

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

A ping mechanism allows the server to verify that connected clients are still alive.
From within tool, resource, prompt, or completion handlers:

```java
(exchange, request) -> {
    exchange.ping();
}
```

### Keep Alive

The server can optionally issue periodic pings to connected clients to verify connection health.

By default, keep-alive is disabled. To enable it, set `keep-alive-interval` in configuration:

```yaml
spring:
  ai:
    mcp:
      server:
        keep-alive-interval: 30s
```

## Usage Examples

### Standard STDIO Server Configuration

```yaml
# Using spring-ai-starter-mcp-server
spring:
  ai:
    mcp:
      server:
        name: stdio-mcp-server
        version: 1.0.0
        type: SYNC
```

### WebMVC Server Configuration

```yaml
# Using spring-ai-starter-mcp-server-webmvc
spring:
  ai:
    mcp:
      server:
        name: webmvc-mcp-server
        version: 1.0.0
        type: SYNC
        instructions: "This server provides weather information tools and resources"
        capabilities:
          tool: true
          resource: true
          prompt: true
          completion: true
        # SSE properties
        sse-message-endpoint: /mcp/messages
        keep-alive-interval: 30s
```

### WebFlux Server Configuration

```yaml
# Using spring-ai-starter-mcp-server-webflux
spring:
  ai:
    mcp:
      server:
        name: webflux-mcp-server
        version: 1.0.0
        type: ASYNC  # Recommended for reactive applications
        instructions: "This reactive server provides weather information tools and resources"
        capabilities:
          tool: true
          resource: true
          prompt: true
          completion: true
        # SSE properties
        sse-message-endpoint: /mcp/messages
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
```

```java
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
Multiple beans can produce tool callbacks, and auto-configuration merges them.

## Example Applications

- Weather Server (WebFlux): Spring AI MCP Server Boot Starter with WebFlux transport
- Weather Server (STDIO): Spring AI MCP Server Boot Starter with STDIO transport
- Weather Server Manual Configuration: Spring AI MCP Server Boot Starter using the Java SDK directly instead of auto-configuration
