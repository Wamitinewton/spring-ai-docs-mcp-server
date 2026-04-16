---
title: "MCP Annotations"
category: "MCP"
source: "MCP Annotations __ Spring AI Reference.pdf"
generated_by: "springai-kb-converter"
---

# MCP Annotations

Spring AI MCP Annotations provides an annotation-driven programming model for Model Context Protocol (MCP) servers and clients in Java.

The goal is to reduce boilerplate while keeping MCP handlers declarative, readable, and easy to register with Spring Boot auto-configuration.

## What It Covers

The module builds on top of the MCP Java SDK and adds a higher-level programming model for common server and client tasks.

### Server Annotations

Use these annotations to expose MCP server capabilities:

- `@McpTool` for tools with generated JSON schema
- `@McpResource` for URI-based resources
- `@McpPrompt` for prompt generation
- `@McpComplete` for completion suggestions

### Client Annotations

Use these annotations to handle MCP client notifications and requests:

- `@McpLogging` for logging notifications
- `@McpSampling` for sampling requests
- `@McpElicitation` for user input collection
- `@McpProgress` for progress notifications
- `@McpToolListChanged` for tool list updates
- `@McpResourceListChanged` for resource list updates
- `@McpPromptListChanged` for prompt list updates

### Special Parameters

The module also supports special parameter types that are injected by the framework and excluded from JSON schema generation.

Common examples include:

- `McpSyncRequestContext`
- `McpAsyncRequestContext`
- `McpTransportContext`
- `McpMeta`
- `@McpProgressToken`
- `CallToolRequest`

For details and examples, see [MCP Annotations Special Parameters](mcp-annotations-special-parameters.md).

## Dependencies

Add the MCP annotations dependency directly if you are not using one of the MCP Boot Starters:

```xml
<dependency>
    <groupId>org.springframework.ai</groupId>
    <artifactId>spring-ai-mcp-annotations</artifactId>
</dependency>
```

If you use one of the MCP Boot Starters, the annotations module is included automatically.

Typical starter packages include:

```text
spring-ai-starter-mcp-client
spring-ai-starter-mcp-client-webflux
spring-ai-starter-mcp-server
spring-ai-starter-mcp-server-webflux
spring-ai-starter-mcp-server-webmvc
```

## Configuration

Annotation scanning is enabled by default when using the MCP Boot Starters.

You can control scanning with application properties:

```yaml
spring:
  ai:
    mcp:
      client:
        annotation-scanner:
          enabled: true
      server:
        annotation-scanner:
          enabled: true
```

## Quick Example

A simple calculator tool can be implemented with `@McpTool` methods:

```java
@Component
public class CalculatorTools {

    @McpTool(name = "add", description = "Add two numbers")
    public int add(
            @McpToolParam(description = "First number", required = true) int a,
            @McpToolParam(description = "Second number", required = true) int b) {
        return a + b;
    }

    @McpTool(name = "multiply", description = "Multiply two numbers")
    public double multiply(
            @McpToolParam(description = "First number", required = true) double x,
            @McpToolParam(description = "Second number", required = true) double y) {
        return x * y;
    }
}
```

A client can handle logging notifications with `@McpLogging`:

```java
@Component
public class LoggingHandler {

    @McpLogging(clients = "my-server")
    public void handleLoggingMessage(LoggingMessageNotification notification) {
        System.out.println("Received log: " + notification.level() + " - " + notification.data());
    }
}
```

## Related Pages

- [MCP Annotations Examples](mcp-annotations-examples.md)
- [MCP Annotations Special Parameters](mcp-annotations-special-parameters.md)
