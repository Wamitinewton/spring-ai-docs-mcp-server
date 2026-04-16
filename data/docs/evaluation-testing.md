---
title: "Evaluation Testing"
category: "Testing"
source: "Evaluation Testing __ Spring AI Reference.pdf"
generated_by: "springai-kb-converter"
---

# Evaluation Testing

Testing AI applications requires evaluating generated content to verify that the model response is grounded in the provided context and does not hallucinate.

One common approach is to use an AI model as an evaluator. The model used for evaluation does not need to be the same model that generated the original response.

Spring AI exposes the evaluation contract through the `Evaluator` interface:

```java
@FunctionalInterface
public interface Evaluator {
    EvaluationResponse evaluate(EvaluationRequest evaluationRequest);
}
```

The input to an evaluation is an `EvaluationRequest`, which carries the user question, optional context, and the response being evaluated:

```java
public class EvaluationRequest {
    private final String userText;
    private final List<Content> dataList;
    private final String responseContent;

    public EvaluationRequest(String userText, List<Content> dataList, String responseContent) {
        this.userText = userText;
        this.dataList = dataList;
        this.responseContent = responseContent;
    }
}
```

- `userText`: the raw input from the user as a `String`
- `dataList`: contextual data, such as retrieved documents from a RAG flow
- `responseContent`: the AI model response to be evaluated as a `String`

## Relevancy Evaluator

The `RelevancyEvaluator` is an implementation of `Evaluator` designed to assess whether a response is relevant to the user input and the retrieved context. It is especially useful for validating RAG flows.

The evaluation uses the user input, the model response, and the retrieved context. Internally, it applies a prompt template that asks the evaluation model to decide whether the response is in line with the provided context.

The default template is structured as follows:

```text
Your task is to evaluate if the response for the query
is in line with the context information provided.

Answer YES, if the response for the query
is in line with context information otherwise NO.

Query:
{query}

Response:
{response}

Context:
{context}

Answer:
```

You can customize the prompt by providing your own `PromptTemplate` via the `.promptTemplate()` builder method.

## Usage in Integration Tests

The following example shows how `RelevancyEvaluator` can be used in an integration test to validate the output of a RAG flow built with `RetrievalAugmentationAdvisor`:

```java
@Test
void evaluateRelevancy() {
    String question = "Where does the adventure of Anacletus and Birba take place?";

    RetrievalAugmentationAdvisor ragAdvisor = RetrievalAugmentationAdvisor.builder()
        .documentRetriever(VectorStoreDocumentRetriever.builder()
            .vectorStore(pgVectorStore)
            .build())
        .build();

    ChatResponse chatResponse = ChatClient.builder(chatModel).build()
        .prompt(question)
        .advisors(ragAdvisor)
        .call()
        .chatResponse();

    EvaluationRequest evaluationRequest = new EvaluationRequest(
        question,
        chatResponse.getMetadata().get(RetrievalAugmentationAdvisor.DOCUMENT_CONTEXT),
        chatResponse.getResult().getOutput().getText()
    );

    RelevancyEvaluator evaluator = new RelevancyEvaluator(ChatClient.builder(chatModel));
    EvaluationResponse evaluationResponse = evaluator.evaluate(evaluationRequest);

    assertThat(evaluationResponse.isPass()).isTrue();
}
```

Spring AI projects commonly use this evaluator to test the output of `QuestionAnswerAdvisor` and `RetrievalAugmentationAdvisor` flows.

### Custom Prompt Template

The `RelevancyEvaluator` uses a default template, but you can override it with a custom `PromptTemplate` built from any supported `TemplateRenderer` implementation.

The template must define these placeholders:

- `query` for the user question
- `response` for the model response
- `context` for the retrieved context

## Fact Checking Evaluator

The `FactCheckingEvaluator` is another implementation of `Evaluator` that checks whether a response is factually supported by the supplied context. It is intended to help detect hallucinations by verifying a claim against a document.

The claim and document are passed to the evaluation model. A smaller model dedicated to this task can be a good fit when you want to reduce evaluation cost. For example, Bespoke's Minicheck can be used through Ollama.

### Usage

The constructor takes a `ChatClient.Builder`:

```java
public FactCheckingEvaluator(ChatClient.Builder chatClientBuilder) {
    this.chatClientBuilder = chatClientBuilder;
}
```

The default prompt template is:

```text
Document: {document}
Claim: {claim}
```

Here, `{document}` is the context information and `{claim}` is the response being evaluated.

### Example

The following example shows a fact-checking evaluation with an Ollama-based chat model:

```java
@Test
void testFactChecking() {
    // Set up the Ollama API
    OllamaApi ollamaApi = new OllamaApi("http://localhost:11434");

    ChatModel chatModel = new OllamaChatModel(
        ollamaApi,
        OllamaChatOptions.builder()
            .model(BESPOKE_MINICHECK)
            .numPredict(2)
            .temperature(0.0d)
            .build()
    );

    // Create the FactCheckingEvaluator
    FactCheckingEvaluator factCheckingEvaluator = new FactCheckingEvaluator(ChatClient.builder(chatModel));

    // Example context and claim
    String context = "The Earth is the third planet from the Sun and the only astronomical object known to harbor life.";
    String claim = "The Earth is the fourth planet from the Sun.";

    // Create an EvaluationRequest
    EvaluationRequest evaluationRequest = new EvaluationRequest(context, Collections.emptyList(), claim);

    // Perform the evaluation
    EvaluationResponse evaluationResponse = factCheckingEvaluator.evaluate(evaluationRequest);

    assertFalse(evaluationResponse.isPass(), "The claim should not be supported by the context");
}
```

## Summary

Use `RelevancyEvaluator` when you want to measure response quality against retrieved context in a RAG flow. Use `FactCheckingEvaluator` when you need a stronger factuality check against a supporting document.
