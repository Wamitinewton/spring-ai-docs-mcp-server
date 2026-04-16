---
title: "MCP Security"
category: "MCP"
source: "MCP Security __ Spring AI Reference.pdf"
generated_by: "springai-kb-converter"
---

# MCP Security

The Spring AI MCP Security project provides OAuth 2.0 and API key-based security support for Model Context Protocol implementations in Spring AI.

This is a community-driven project, still evolving, and it currently targets the Spring AI 1.1.x line. It is not yet an official Spring AI or MCP project component.

## What It Provides

The project is split into three areas:

- MCP server security
- MCP client security
- MCP authorization server support

Together, these modules help secure MCP servers and clients, and they add MCP-aware authorization-server features such as dynamic client registration and resource indicators.

## MCP Server Security

The server-side module provides OAuth 2.0 resource-server support and basic API key authentication for Spring AI MCP servers.

It is intended for WebMVC-based servers.

### Dependencies

```xml
<dependencies>
    <dependency>
        <groupId>org.springaicommunity</groupId>
        <artifactId>mcp-server-security</artifactId>
    </dependency>
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-security</artifactId>
    </dependency>
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-oauth2-resource-server</artifactId>
    </dependency>
</dependencies>
```

### OAuth 2.0 Resource Server

A typical setup enables authentication on incoming requests and configures the MCP security customizer with the authorization-server issuer.

```java
@Configuration
@EnableWebSecurity
@EnableMethodSecurity
class McpServerConfiguration {

    @Value("${spring.security.oauth2.resourceserver.jwt.issuer-uri}")
    private String issuerUrl;

    @Bean
    SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        return http
                .authorizeHttpRequests(auth -> auth.anyRequest().authenticated())
                .with(
                        McpServerOAuth2Configurer.mcpServerOAuth2(),
                        mcpAuthorization -> {
                            mcpAuthorization.authorizationServer(issuerUrl);
                            mcpAuthorization.validateAudienceClaim(true);
                        }
                )
                .build();
    }
}
```

If you want to secure only tool invocations while leaving discovery endpoints public, use method security and annotate tool handlers with `@PreAuthorize`.

```java
@Service
public class MyToolsService {

    @PreAuthorize("isAuthenticated()")
    @McpTool(name = "greeter", description = "A tool that greets you in the selected language")
    public String greet(@ToolParam(description = "Language") String language) {
        if (!StringUtils.hasText(language)) {
            language = "";
        }

        return switch (language.toLowerCase()) {
            case "english" -> "Hello you!";
            case "french" -> "Salut toi!";
            default -> "I don't understand language \"%s\". So I'm just going to say Hello!".formatted(language);
        };
    }
}
```

You can also inspect the current authenticated principal directly from the security context.

```java
@McpTool(name = "greeter", description = "Greets the user by name")
@PreAuthorize("isAuthenticated()")
public String greet(@ToolParam(description = "Language") String language) {
    var authentication = SecurityContextHolder.getContext().getAuthentication();
    var name = authentication.getName();

    return switch (language.toLowerCase()) {
        case "english" -> "Hello, %s!".formatted(name);
        case "french" -> "Salut %s!".formatted(name);
        default -> "I don't understand language \"%s\". So I'm just going to say Hello %s!".formatted(language, name);
    };
}
```

### API Key Authentication

The project also supports API key authentication through a repository of API key entities.

A simple in-memory repository is available for samples and local development, but the bcrypt-backed implementation is not recommended for production workloads.

```java
@Configuration
@EnableWebSecurity
class McpServerConfiguration {

    @Bean
    SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        return http
                .authorizeHttpRequests(auth -> auth.anyRequest().authenticated())
                .with(
                        mcpServerApiKey(),
                        apiKey -> apiKey.apiKeyRepository(apiKeyRepository())
                )
                .build();
    }

    @Bean
    ApiKeyEntityRepository<ApiKeyEntityImpl> apiKeyRepository() {
        var apiKey = ApiKeyEntityImpl.builder()
                .name("test api key")
                .id("api01")
                .secret("mycustomapikey")
                .build();

        return new InMemoryApiKeyEntityRepository<>(List.of(apiKey));
    }
}
```

With this setup, the client can authenticate using a header such as `X-API-key: api01.mycustomapikey`.

### Known Limitations

- SSE transport is not supported on the server side.
- Use Streamable HTTP or stateless transport instead.

## MCP Client Security

The client-side module adds OAuth 2.0 support for Spring AI MCP clients.

It works with the `spring-ai-starter-mcp-client` and `spring-ai-starter-mcp-client-webflux` starters.

### Dependencies

```xml
<dependency>
    <groupId>org.springaicommunity</groupId>
    <artifactId>mcp-client-security</artifactId>
</dependency>
```

### Supported OAuth 2.0 Flows

The client module supports three flows:

- Authorization code flow for user-driven access
- Client credentials flow for machine-to-machine access
- Hybrid flow for cases where discovery happens without a user but tool calls require user-level permissions

### Common Setup

For OAuth 2.0 client support, enable Spring Security OAuth2 client properties and keep the MCP client in sync mode when you rely on startup-time tool discovery.

```properties
spring.ai.mcp.client.type=SYNC

spring.security.oauth2.client.registration.authserver.client-id=<THE CLIENT ID>
spring.security.oauth2.client.registration.authserver.client-secret=<THE CLIENT SECRET>
spring.security.oauth2.client.registration.authserver.authorization-grant-type=authorization_code
spring.security.oauth2.client.registration.authserver.provider=authserver

spring.security.oauth2.client.provider.authserver.issuer-uri=<THE ISSUER URI OF YOUR AUTH SERVER>
```

For client credentials, use a separate registration with `authorization-grant-type=client_credentials`.

### HttpClient-Based Clients

For the standard MCP client starter, configure a `McpSyncHttpClientRequestCustomizer` and an OAuth2 request customizer.

```java
@Configuration
class McpConfiguration {

    @Bean
    McpSyncClientCustomizer syncClientCustomizer() {
        return (name, syncSpec) -> syncSpec.transportContextProvider(
                new AuthenticationMcpTransportContextProvider()
        );
    }

    @Bean
    McpSyncHttpClientRequestCustomizer requestCustomizer(OAuth2AuthorizedClientManager clientManager) {
        return new OAuth2AuthorizationCodeSyncHttpRequestCustomizer(clientManager, "authserver");
    }
}
```

Available request customizers include:

- `OAuth2AuthorizationCodeSyncHttpRequestCustomizer`
- `OAuth2ClientCredentialsSyncHttpRequestCustomizer`
- `OAuth2HybridSyncHttpRequestCustomizer`

### WebClient-Based Clients

For the WebFlux starter, configure a `WebClient.Builder` with an MCP OAuth2 filter.

```java
@Configuration
class McpConfiguration {

    @Bean
    WebClient.Builder mcpWebClientBuilder(OAuth2AuthorizedClientManager clientManager) {
        return WebClient.builder().filter(
                new McpOAuth2AuthorizationCodeExchangeFilterFunction(clientManager, "authserver")
        );
    }
}
```

Available filter functions include:

- `McpOAuth2AuthorizationCodeExchangeFilterFunction`
- `McpOAuth2ClientCredentialsExchangeFilterFunction`
- `McpOAuth2HybridExchangeFilterFunction`

### Working Around Spring AI Auto-Configuration

Spring AI may initialize MCP clients at startup, which can be awkward for user-based authentication flows.

Two common workarounds are:

- publish an empty `ToolCallbackResolver` bean to disable tool auto-configuration
- create the MCP client programmatically instead of relying on properties-based bootstrap

A programmatic HttpClient-based setup looks like this:

```java
@Bean
McpSyncClient client(
        ObjectMapper objectMapper,
        McpSyncHttpClientRequestCustomizer requestCustomizer,
        McpClientCommonProperties commonProps
) {
    var transport = HttpClientStreamableHttpTransport.builder(mcpServerUrl)
            .clientBuilder(HttpClient.newBuilder())
            .jsonMapper(new JacksonMcpJsonMapper(objectMapper))
            .httpRequestCustomizer(requestCustomizer)
            .build();

    var clientInfo = new McpSchema.Implementation("client-name", commonProps.getVersion());

    return McpClient.sync(transport)
            .clientInfo(clientInfo)
            .requestTimeout(commonProps.getRequestTimeout())
            .transportContextProvider(new AuthenticationMcpTransportContextProvider())
            .build();
}
```

A WebClient-based setup follows the same idea using `WebClientStreamableHttpTransport`.

## MCP Authorization Server

The authorization-server module extends Spring Authorization Server with MCP-aware capabilities such as dynamic client registration and resource indicators.

### Dependency

```xml
<dependency>
    <groupId>org.springaicommunity</groupId>
    <artifactId>mcp-authorization-server</artifactId>
</dependency>
```

### Configuration

A minimal configuration enables authorization-server behavior and form login for the built-in user.

```java
@Bean
SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
    return http
            .authorizeHttpRequests(auth -> auth.anyRequest().authenticated())
            .with(McpAuthorizationServerConfigurer.mcpAuthorizationServer(), withDefaults())
            .formLogin(withDefaults())
            .build();
}
```

A typical application also sets a dedicated session cookie name when running multiple local Spring applications.

## Samples and Integrations

The project includes sample applications and integration tests covering the supported modules.

It can be used with tools such as:

- Claude Desktop
- MCP Inspector
- Cursor

When using MCP Inspector, you may need to relax CSRF and CORS settings for local development.

## Notes

- This project is community-driven and may change.
- It currently targets Spring AI 1.1.x.
- Prefer Streamable HTTP or stateless transport for newer server deployments.
- Use the client and server modules together only when your authentication model supports the discovery and tool-call split.
