---
title: "MCP Client Boot Starter"
category: "MCP"
source: "MCP Client Boot Starter __ Spring AI Reference.pdf"
generated_by: "springai-kb-converter"
---

# MCP Client Boot Starter

The Spring AI MCP Client Boot Starter provides auto-configuration for MCP client functionality in Spring Boot applications.

It supports both synchronous and asynchronous client modes, multiple transport types, automatic client initialization, tool callback integration, and several customization hooks for advanced deployments.

## Starters

### Standard MCP Client

Use the standard starter for JVM-based MCP client support.

```xml
<dependency>
    <groupId>org.springframework.ai</groupId>
    <artifactId>spring-ai-starter-mcp-client</artifactId>
</dependency>
```

The standard starter supports `STDIO`, `SSE`, `Streamable HTTP`, and `Stateless Streamable HTTP` transports.

### WebFlux MCP Client

Use the WebFlux starter when you want reactive transport support.

```xml
<dependency>
    <groupId>org.springframework.ai</groupId>
    <artifactId>spring-ai-starter-mcp-client-webflux</artifactId>
</dependency>
```

The WebFlux starter provides the same client features with reactive transport implementations.

## Core Features

- multiple named client connections
- automatic client initialization
- synchronous or asynchronous client mode
- transport support for STDIO, SSE, and Streamable HTTP
- automatic registration of annotated client handlers
- tool callback integration with Spring AI
- tool filtering and tool name prefixing
- client customization hooks for advanced behavior

## Configuration Properties

The common client properties are prefixed with `spring.ai.mcp.client`.

### General Settings

```yaml
spring:
  ai:
    mcp:
      client:
        enabled: true
        name: my-mcp-client
        version: 1.0.0
        initialized: true
        request-timeout: 20s
        type: SYNC
```

The `type` property must be either `SYNC` or `ASYNC`. A single application should not mix sync and async client modes.

### Annotation Scanning

```yaml
spring:
  ai:
    mcp:
      client:
        annotation-scanner:
          enabled: true
```

This enables automatic discovery of `@McpLogging`, `@McpSampling`, `@McpElicitation`, `@McpProgress`, and the other client annotations.

### Transport Configuration

#### STDIO

```yaml
spring:
  ai:
    mcp:
      client:
        stdio:
          root-change-notification: true
          connections:
            server1:
              command: /path/to/server
              args:
                - --port=8080
                - --mode=production
              env:
                API_KEY: your-api-key
                DEBUG: "true"
```

#### SSE

```yaml
spring:
  ai:
    mcp:
      client:
        sse:
          connections:
            server1:
              url: http://localhost:8080
            server2:
              url: http://localhost:8081
              sse-endpoint: /custom-sse
```

#### Streamable HTTP

```yaml
spring:
  ai:
    mcp:
      client:
        streamable-http:
          connections:
            server1:
              url: http://localhost:8082
            server2:
              url: http://localhost:8083
              endpoint: /mcp
```

For SSE and Streamable HTTP, split the base URL and the endpoint path when your server exposes a custom event or stream endpoint.

## Client Customization

You can customize client behavior by providing an `McpSyncClientCustomizer` or `McpAsyncClientCustomizer` bean.

```java
@Component
public class CustomMcpSyncClientCustomizer implements McpSyncClientCustomizer {

    @Override
    public void customize(String serverConfigurationName, McpClient.SyncSpec spec) {
        spec.requestTimeout(Duration.ofSeconds(30));

        spec.sampling((CreateMessageRequest request) -> CreateMessageResult.builder()
                .role(Role.ASSISTANT)
                .content(new TextContent(generateLLMResponse(request)))
                .model("gpt-4")
                .build());

        spec.elicitation((ElicitRequest request) ->
                new ElicitResult(ElicitResult.Action.ACCEPT, Map.of("message", request.message())));

        spec.progressConsumer(progress -> {
            // Handle progress notifications
        });

        spec.toolsChangeConsumer(tools -> {
            // Handle tool changes
        });

        spec.resourcesChangeConsumer(resources -> {
            // Handle resource changes
        });

        spec.promptsChangeConsumer(prompts -> {
            // Handle prompt changes
        });

        spec.loggingConsumer(log -> {
            // Handle logs
        });
    }
}
```

The `serverConfigurationName` argument identifies the connection that the customizer is applied to.

## Tool Callback Support

When tool callback integration is enabled, MCP tools can be exposed through Spring AI tool callbacks.

The starter also supports tool filtering and tool name prefixing.

### Tool Filtering

Implement `McpToolFilter` to include or exclude tools based on connection metadata or tool properties.

```java
@Component
public class CustomMcpToolFilter implements McpToolFilter {

    @Override
    public boolean test(McpConnectionInfo connectionInfo, McpSchema.Tool tool) {
        if (connectionInfo.clientInfo().name().equals("restricted-client")) {
            return false;
        }

        if (tool.name().startsWith("allowed_")) {
            return true;
        }

        if (tool.description() != null && tool.description().contains("experimental")) {
            return false;
        }

        return true;
    }
}
```

Only one `McpToolFilter` bean should be registered. If you need multiple rules, combine them in one composite filter.

### Tool Name Prefix Generation

Use `McpToolNamePrefixGenerator` to avoid naming conflicts when tools from multiple servers expose the same tool name.

```java
@Component
public class CustomToolNamePrefixGenerator implements McpToolNamePrefixGenerator {

    @Override
    public String prefixedToolName(McpConnectionInfo connectionInfo, Tool tool) {
        String serverName = connectionInfo.initializeResult().serverInfo().name();
        String serverVersion = connectionInfo.initializeResult().serverInfo().version();
        return serverName + "_v" + serverVersion.replace(".", "_") + "_" + tool.name();
    }
}
```

To disable prefixing entirely, register `McpToolNamePrefixGenerator.noPrefix()` as a bean.

### Tool Context to MCP Metadata Conversion

The starter can convert Spring AI `ToolContext` values into MCP metadata through `ToolContextToMcpMetaConverter`.

```java
@Component
public class CustomToolContextToMcpMetaConverter implements ToolContextToMcpMetaConverter {

    @Override
    public Map<String, Object> convert(ToolContext toolContext) {
        if (toolContext == null || toolContext.getContext() == null) {
            return Map.of();
        }

        Map<String, Object> metadata = new HashMap<>();
        for (Map.Entry<String, Object> entry : toolContext.getContext().entrySet()) {
            if (entry.getValue() != null) {
                metadata.put("app_" + entry.getKey(), entry.getValue());
            }
        }

        metadata.put("timestamp", System.currentTimeMillis());
        metadata.put("source", "spring-ai");
        return metadata;
    }
}
```

## MCP Client Annotations

The boot starter can automatically discover annotated client handlers when annotation scanning is enabled.

Common annotations include:

- `@McpLogging`
- `@McpSampling`
- `@McpElicitation`
- `@McpProgress`
- `@McpToolListChanged`
- `@McpResourceListChanged`
- `@McpPromptListChanged`

For examples, see [MCP Client Annotations](mcp-client-annotations.md).

## Usage Example

```java
@Autowired
private List<McpSyncClient> mcpSyncClients;

@Autowired
private SyncMcpToolCallbackProvider toolCallbackProvider;
```

When the application context starts, the starter creates and registers the configured MCP clients, applies any customizers, and exposes tool callbacks when enabled.

## Notes

- Use the standard starter for blocking applications.
- Use the WebFlux starter for reactive applications.
- Prefer `SSE` or `Streamable HTTP` for production transports where applicable.
- Match annotation `clients` values to the configured connection names.
- If you disable tool callback auto-configuration, no `ToolCallbackProvider` bean is created.
