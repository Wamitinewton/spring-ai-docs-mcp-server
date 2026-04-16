---
title: "MCP Annotations Examples"
category: "MCP"
source: "MCP Annotations Examples __ Spring AI Reference.pdf"
generated_by: "springai-kb-converter"
---

# MCP Annotations Examples

This page collects practical examples of using MCP annotations in Spring AI applications.

If you need the annotation reference itself, see the main MCP annotations guide in this repository.

## Simple Calculator Server

This example shows an MCP server that exposes calculator tools.

```java
@SpringBootApplication
public class CalculatorServerApplication {

    public static void main(String[] args) {
        SpringApplication.run(CalculatorServerApplication.class, args);
    }
}

@Component
public class CalculatorTools {

    @McpTool(name = "add", description = "Add two numbers")
    public double add(
            @McpToolParam(description = "First number", required = true) double a,
            @McpToolParam(description = "Second number", required = true) double b) {
        return a + b;
    }

    @McpTool(name = "subtract", description = "Subtract two numbers")
    public double subtract(
            @McpToolParam(description = "First number", required = true) double a,
            @McpToolParam(description = "Second number", required = true) double b) {
        return a - b;
    }

    @McpTool(name = "multiply", description = "Multiply two numbers")
    public double multiply(
            @McpToolParam(description = "First number", required = true) double a,
            @McpToolParam(description = "Second number", required = true) double b) {
        return a * b;
    }

    @McpTool(name = "divide", description = "Divide two numbers")
    public double divide(
            @McpToolParam(description = "Dividend", required = true) double dividend,
            @McpToolParam(description = "Divisor", required = true) double divisor) {
        if (divisor == 0) {
            throw new IllegalArgumentException("Division by zero");
        }
        return dividend / divisor;
    }

    @McpTool(name = "calculate-expression", description = "Calculate a complex mathematical expression")
    public CallToolResult calculateExpression(
            CallToolRequest request,
            McpSyncRequestContext context) {
        Map<String, Object> args = request.arguments();
        String expression = (String) args.get("expression");

        context.info("Calculating: " + expression);

        try {
            double result = evaluateExpression(expression);
            return CallToolResult.builder()
                    .addTextContent("Result: " + result)
                    .build();
        } catch (Exception e) {
            return CallToolResult.builder()
                    .isError(true)
                    .addTextContent("Error: " + e.getMessage())
                    .build();
        }
    }
}
```

Example configuration:

```yaml
spring:
  ai:
    mcp:
      server:
        name: calculator-server
        version: 1.0.0
        type: SYNC
        protocol: SSE
        capabilities:
          tool: true
          resource: true
          prompt: true
          completion: true
```

## Document Processing Server

This example combines resources, tools, prompts, completion, and request metadata handling.

```java
@Component
public class DocumentServer {

    private final Map<String, Document> documents = new ConcurrentHashMap<>();

    @McpResource(
            uri = "document://{id}",
            name = "Document",
            description = "Access stored documents")
    public ReadResourceResult getDocument(String id, McpMeta meta) {
        Document doc = documents.get(id);
        if (doc == null) {
            return new ReadResourceResult(List.of(
                    new TextResourceContents("document://" + id, "text/plain", "Document not found")
            ));
        }

        String accessLevel = (String) meta.get("accessLevel");
        if ("restricted".equals(doc.getClassification()) && !"admin".equals(accessLevel)) {
            return new ReadResourceResult(List.of(
                    new TextResourceContents("document://" + id, "text/plain", "Access denied")
            ));
        }

        return new ReadResourceResult(List.of(
                new TextResourceContents("document://" + id, doc.getMimeType(), doc.getContent())
        ));
    }

    @McpTool(name = "analyze-document", description = "Analyze document content")
    public String analyzeDocument(
            McpSyncRequestContext context,
            @McpToolParam(description = "Document ID", required = true) String docId,
            @McpToolParam(description = "Analysis type", required = false) String type) {

        Document doc = documents.get(docId);
        if (doc == null) {
            return "Document not found";
        }

        String progressToken = context.request().progressToken();
        if (progressToken != null) {
            context.progress(p -> p.progress(0.0).total(1.0).message("Starting analysis"));
        }

        String analysisType = type != null ? type : "summary";
        String result = performAnalysis(doc, analysisType);

        if (progressToken != null) {
            context.progress(p -> p.progress(1.0).total(1.0).message("Analysis complete"));
        }

        return result;
    }

    @McpPrompt(name = "document-summary", description = "Generate document summary prompt")
    public GetPromptResult documentSummaryPrompt(
            @McpArg(name = "docId", required = true) String docId,
            @McpArg(name = "length", required = false) String length) {

        Document doc = documents.get(docId);
        if (doc == null) {
            return new GetPromptResult("Error",
                    List.of(new PromptMessage(Role.SYSTEM, new TextContent("Document not found"))));
        }

        String promptText = String.format(
                "Please summarize the following document in %s:\n\n%s",
                length != null ? length : "a few paragraphs",
                doc.getContent()
        );

        return new GetPromptResult("Document Summary",
                List.of(new PromptMessage(Role.USER, new TextContent(promptText))));
    }

    @McpComplete(prompt = "document-summary")
    public List<String> completeDocumentId(String prefix) {
        return documents.keySet().stream()
                .filter(id -> id.startsWith(prefix))
                .sorted()
                .limit(10)
                .toList();
    }
}
```

## MCP Client Handlers

This example shows a client application that handles logging, sampling, elicitation, progress, and tool/resource list changes.

```java
@SpringBootApplication
public class McpClientApplication {

    public static void main(String[] args) {
        SpringApplication.run(McpClientApplication.class, args);
    }
}

@Component
public class ClientHandlers {

    private final Logger logger = LoggerFactory.getLogger(ClientHandlers.class);
    private final ProgressTracker progressTracker = new ProgressTracker();
    private final ChatModel chatModel;

    public ClientHandlers(@Lazy ChatModel chatModel) {
        this.chatModel = chatModel;
    }

    @McpLogging(clients = "server1")
    public void handleLogging(LoggingMessageNotification notification) {
        switch (notification.level()) {
            case ERROR -> logger.error("[MCP] {} - {}", notification.logger(), notification.data());
            case WARNING -> logger.warn("[MCP] {} - {}", notification.logger(), notification.data());
            case INFO -> logger.info("[MCP] {} - {}", notification.logger(), notification.data());
            default -> logger.debug("[MCP] {} - {}", notification.logger(), notification.data());
        }
    }

    @McpSampling(clients = "server1")
    public CreateMessageResult handleSampling(CreateMessageRequest request) {
        List<Message> messages = request.messages().stream()
                .map(msg -> {
                    if (msg.role() == Role.USER) {
                        return new UserMessage(((TextContent) msg.content()).text());
                    }
                    return AssistantMessage.builder()
                            .content(((TextContent) msg.content()).text())
                            .build();
                })
                .toList();

        ChatResponse response = chatModel.call(new Prompt(messages));

        return CreateMessageResult.builder()
                .role(Role.ASSISTANT)
                .content(new TextContent(response.getResult().getOutput().getText()))
                .model(request.modelPreferences().hints().get(0).name())
                .build();
    }

    @McpElicitation(clients = "server1")
    public ElicitResult handleElicitation(ElicitRequest request) {
        logger.info("Elicitation requested: {}", request.message());

        Map<String, Object> userData = new HashMap<>();
        Map<String, Object> schema = request.requestedSchema();
        if (schema != null && schema.containsKey("properties")) {
            Map<String, Object> properties = (Map<String, Object>) schema.get("properties");
            properties.forEach((key, value) -> userData.put(key, getDefaultValueForProperty(key, value)));
        }

        return new ElicitResult(ElicitResult.Action.ACCEPT, userData);
    }

    @McpProgress(clients = "server1")
    public void handleProgress(ProgressNotification notification) {
        progressTracker.update(
                notification.progressToken(),
                notification.progress(),
                notification.total(),
                notification.message()
        );

        broadcastProgress(notification);
    }

    @McpToolListChanged(clients = "server1")
    public void handleServer1ToolsChanged(List<McpSchema.Tool> tools) {
        logger.info("Server1 tools updated: {} tools available", tools.size());
        toolRegistry.updateServerTools("server1", tools);
        eventBus.publish(new ToolsUpdatedEvent("server1", tools));
    }

    @McpResourceListChanged(clients = "server1")
    public void handleServer1ResourcesChanged(List<McpSchema.Resource> resources) {
        logger.info("Server1 resources updated: {} resources available", resources.size());
        resourceCache.clearServer("server1");
        resources.forEach(resource -> resourceCache.register("server1", resource));
    }
}
```

Example configuration:

```yaml
spring:
  ai:
    mcp:
      client:
        type: SYNC
        initialized: true
        request-timeout: 30s
        annotation-scanner:
          enabled: true
        sse:
          connections:
            server1:
              url: http://localhost:8080
        stdio:
          connections:
            local-tool:
              command: /usr/local/bin/mcp-tool
              args:
                - --mode=production
```

## Async Examples

### Async Tool Server

This example shows reactive MCP handlers for tools and resources.

```java
@Component
public class AsyncDataProcessor {

    @McpTool(name = "fetch-data", description = "Fetch data from external source")
    public Mono<DataResult> fetchData(
            @McpToolParam(description = "Data source URL", required = true) String url,
            @McpToolParam(description = "Timeout in seconds", required = false) Integer timeout) {

        Duration timeoutDuration = Duration.ofSeconds(timeout != null ? timeout : 30);

        return WebClient.create()
                .get()
                .uri(url)
                .retrieve()
                .bodyToMono(String.class)
                .map(data -> new DataResult(url, data, System.currentTimeMillis()))
                .timeout(timeoutDuration)
                .onErrorReturn(new DataResult(url, "Error fetching data", 0L));
    }

    @McpTool(name = "process-stream", description = "Process data stream")
    public Flux<String> processStream(
            McpAsyncRequestContext context,
            @McpToolParam(description = "Item count", required = true) int count) {

        String progressToken = context.request().progressToken();

        return Flux.range(1, count)
                .delayElements(Duration.ofMillis(100))
                .flatMap(i -> {
                    if (progressToken != null) {
                        double progress = (double) i / count;
                        return context.progress(p -> p.progress(progress).total(1.0).message("Processing item " + i))
                                .thenReturn("Processed item " + i);
                    }
                    return Mono.just("Processed item " + i);
                });
    }

    @McpResource(uri = "async-data://{id}", name = "Async Data")
    public Mono<ReadResourceResult> getAsyncData(String id) {
        return Mono.fromCallable(() -> loadDataAsync(id))
                .subscribeOn(Schedulers.boundedElastic())
                .map(data -> new ReadResourceResult(List.of(
                        new TextResourceContents("async-data://" + id, "application/json", data)
                )));
    }
}
```

### Async Client Handlers

```java
@Component
public class AsyncClientHandlers {

    @McpSampling(clients = "async-server")
    public Mono<CreateMessageResult> handleAsyncSampling(CreateMessageRequest request) {
        return Mono.fromCallable(() -> {
            // convert the request into a Spring AI prompt and call the model
            return CreateMessageResult.builder()
                    .role(Role.ASSISTANT)
                    .content(new TextContent("Async sampling response"))
                    .model(request.modelPreferences().hints().get(0).name())
                    .build();
        });
    }
}
```

## Notes

These examples focus on the annotation patterns most commonly used in Spring AI MCP applications:

- tools for executable operations,
- resources for data access,
- prompts for reusable prompt generation,
- completion for value suggestions,
- client callbacks for logging and interactive flows.
