---
title: "MCP Server Boot Starter"
category: "MCP"
source: "MCP Server Boot Starter __ Spring AI Reference.pdf"
generated_by: "springai-kb-converter"
---

# MCP Server Boot Starter

The Spring AI MCP Server Boot Starter provides auto-configuration for MCP servers in Spring Boot applications.

It supports synchronous and asynchronous server modes, multiple transport options, annotation-based handler registration, and Spring Boot integration with minimal configuration.

## Starters

### Standard MCP Server

Use the standard starter for in-process or JVM-based server setups.

```xml
<dependency>
    <groupId>org.springframework.ai</groupId>
    <artifactId>spring-ai-starter-mcp-server</artifactId>
</dependency>
```

### WebMVC MCP Server

Use the WebMVC starter for servlet-based deployments.

```xml
<dependency>
    <groupId>org.springframework.ai</groupId>
    <artifactId>spring-ai-starter-mcp-server-webmvc</artifactId>
</dependency>
```

### WebFlux MCP Server

Use the WebFlux starter for reactive deployments.

```xml
<dependency>
    <groupId>org.springframework.ai</groupId>
    <artifactId>spring-ai-starter-mcp-server-webflux</artifactId>
</dependency>
```

## Transport and Protocol Options

The server starter supports the following deployment styles:

- `STDIO`
- `SSE`
- `STREAMABLE`
- `STATELESS`

A starter choice and the `spring.ai.mcp.server.protocol` property determine the final server mode.

Example configuration:

```yaml
spring:
  ai:
    mcp:
      server:
        type: SYNC
        annotation-scanner:
          enabled: true
        protocol: STREAMABLE
```

Common combinations include:

- `spring-ai-starter-mcp-server` for `STDIO`
- `spring-ai-starter-mcp-server-webmvc` for `SSE`, `STREAMABLE`, or `STATELESS`
- `spring-ai-starter-mcp-server-webflux` for `SSE`, `STREAMABLE`, or `STATELESS`

## Core Features

- automatic registration of annotated server handlers
- support for tools, resources, prompts, and completions
- sync or async handler selection
- stateful or stateless request handling
- automatic bean scanning and registration
- progress, sampling, logging, and elicitation support where applicable

## Server Capabilities

The starter enables the standard MCP server capabilities:

- tools
- resources
- prompts
- completions
- logging
- progress
- ping

All capabilities are enabled by default unless you explicitly disable them.

## Server Annotations

The boot starter works together with the server annotations module.

Common annotations include:

- `@McpTool`
- `@McpResource`
- `@McpPrompt`
- `@McpComplete`

Special parameters include:

- `McpMeta`
- `@McpProgressToken`
- `McpSyncServerExchange`
- `McpAsyncServerExchange`
- `McpTransportContext`
- `CallToolRequest`

For details and code examples, see [MCP Server Annotations](mcp-server-annotations.md) and [MCP Annotations Special Parameters](mcp-annotations-special-parameters.md).

## Sync and Async Modes

The starter can register either synchronous or asynchronous handlers depending on the configured server type.

### Sync Mode

Sync mode uses non-reactive return types such as primitives, objects, collections, and MCP result types.

### Async Mode

Async mode uses reactive return types such as `Mono<T>`, `Flux<T>`, and `Publisher<T>`.

Keep the method signatures aligned with the configured server type. Mixed sync and async handlers are filtered at startup.

## Example Application

```java
@SpringBootApplication
public class McpServerApplication {

    public static void main(String[] args) {
        SpringApplication.run(McpServerApplication.class, args);
    }
}

@Component
public class MyMcpTools {

    @McpTool(name = "add", description = "Add two numbers")
    public int add(
            @McpToolParam(description = "First number", required = true) int a,
            @McpToolParam(description = "Second number", required = true) int b) {
        return a + b;
    }
}
```

## Boot Integration

With Spring Boot auto-configuration enabled, the starter will:

1. scan for beans annotated with MCP server annotations,
2. register the discovered handlers,
3. apply the configured server type and transport,
4. filter out incompatible methods,
5. expose the server capabilities through the selected transport.

## Configuration Notes

Enable annotation scanning when you want Spring Boot to discover MCP server handlers automatically.

Use `SYNC` mode for traditional request-response handlers and `ASYNC` mode for reactive handlers.

Use `STATELESS` when you want lightweight request handling without bidirectional operations.

## Related Pages

- [MCP Server Annotations](mcp-server-annotations.md)
- [MCP Annotations Special Parameters](mcp-annotations-special-parameters.md)
- [MCP Annotations Examples](mcp-annotations-examples.md)
