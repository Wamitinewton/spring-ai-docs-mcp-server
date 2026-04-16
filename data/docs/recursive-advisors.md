---
title: "Recursive Advisors"
category: "Advisors"
source: "Recursive Advisors __ Spring AI Reference.pdf"
generated_by: "springai-kb-converter"
---

# Recursive Advisors

Recursive advisors are advisors that can re-enter the downstream advisor chain multiple times until a condition is satisfied.

This pattern is useful for workflows such as:

- tool-call loops until no additional tool call is needed
- structured-output validation with retry
- retry policies that adjust prompt or options between attempts
- iterative evaluation flows

## Core Mechanism

The key utility is `CallAdvisorChain.copy(CallAdvisor after)`.

It creates a new sub-chain containing only advisors that appear after the current recursive advisor.

This allows the recursive advisor to invoke the remaining chain repeatedly without re-running upstream advisors.

Benefits:

- preserves advisor ordering
- keeps observability and interception behavior for each iteration
- avoids duplicate execution of earlier advisors

## Built-in Recursive Advisors

Spring AI ships with recursive advisors that demonstrate this approach.

### ToolCallAdvisor

`ToolCallAdvisor` implements tool-calling loops inside the advisor chain instead of relying solely on model-internal tool execution.

Key behavior:

- disables internal tool execution (`setInternalToolExecutionEnabled(false)`)
- loops through the chain until no more tool calls are present
- supports `returnDirect` behavior from tool execution
- uses `callAdvisorChain.copy(this)` for recursive sub-chain calls
- supports configurable conversation history handling

Example:

```java
var toolCallAdvisor = ToolCallAdvisor.builder()
    .toolCallingManager(toolCallingManager)
    .advisorOrder(BaseAdvisor.HIGHEST_PRECEDENCE + 300)
    .build();

var chatClient = ChatClient.builder(chatModel)
    .defaultAdvisors(toolCallAdvisor)
    .build();
```

#### Conversation History Control

`ToolCallAdvisor` can manage loop-time conversation history internally.

- default: `conversationHistoryEnabled=true`
- disable with `.disableMemory()` when a memory advisor already handles history

Example with chat memory advisor:

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

#### Return Direct

When a tool execution returns `returnDirect=true`, the advisor:

1. executes the tool call,
2. exits the loop,
3. returns the tool result directly to the client as response content.

This is useful for low-latency responses or when tool output should not be post-processed by the LLM.

### StructuredOutputValidationAdvisor

`StructuredOutputValidationAdvisor` validates JSON output against a generated schema and retries on failure.

Key behavior:

- generates schema from target output type
- validates model output against that schema
- retries up to `maxRepeatAttempts`
- appends validation feedback on retries to help correction
- uses `callAdvisorChain.copy(this)` for repeated calls

Example:

```java
var validationAdvisor = StructuredOutputValidationAdvisor.builder()
    .outputType(MyResponseType.class)
    .maxRepeatAttempts(3)
    .advisorOrder(BaseAdvisor.HIGHEST_PRECEDENCE + 1000)
    .build();

var chatClient = ChatClient.builder(chatModel)
    .defaultAdvisors(validationAdvisor)
    .build();
```

## Design Guidelines

When implementing your own recursive advisor:

- define a clear termination condition
- keep retry/loop state in advisor context when needed
- use `copy(this)` to recurse only over downstream advisors
- avoid mutating unrelated request parts across iterations
- keep max iteration count bounded to prevent infinite loops

## Operational Considerations

- Recursive advisors can increase token usage and latency.
- Emit clear logs/metrics per iteration for observability.
- Combine with memory advisors carefully to avoid duplicated context.
- Keep advisor ordering explicit so recursive behavior is predictable.

## When to Use

Use recursive advisors when iterative control over model calls must remain observable and composable in the advisor chain.

If the model can solve the flow internally without cross-advisor visibility, a non-recursive strategy may be simpler.
