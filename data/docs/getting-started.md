---
title: "Getting Started"
category: "Getting Started"
source: "Getting Started __ Spring AI Reference.pdf"
generated_by: "springai-kb-converter"
---

# Getting Started

This guide collects the main entry points for starting a Spring AI project.

Choose the sections that apply to your setup:

- creating a project from Spring Initializr,
- configuring Maven repositories,
- importing the Spring AI BOM,
- adding dependencies for specific capabilities,
- finding examples and samples.

## Spring Initializr

Start with [start.spring.io](https://start.spring.io) and select the AI models, vector stores, and other Spring AI components you want in your application.

## Artifact Repositories

### Releases

Spring AI 1.0.0 and later are available from Maven Central. In most Maven and Gradle builds, no extra repository configuration is required.

If you need to declare Maven Central explicitly, the repository entry looks like this:

```xml
<repositories>
    <repository>
        <id>central</id>
        <name>Maven Central</name>
        <url>https://repo.maven.apache.org/maven2</url>
    </repository>
</repositories>
```

### Snapshots

To use snapshot or milestone builds, add the Spring snapshot repositories to your build.

```xml
<repositories>
    <repository>
        <id>spring-snapshots</id>
        <name>Spring Snapshots</name>
        <url>https://repo.spring.io/snapshot</url>
        <releases>
            <enabled>false</enabled>
        </releases>
    </repository>
    <repository>
        <id>central-portal-snapshots</id>
        <name>Central Portal Snapshots</name>
        <url>https://central.sonatype.com/repository/maven-snapshots/</url>
        <releases>
            <enabled>false</enabled>
        </releases>
        <snapshots>
            <enabled>true</enabled>
        </snapshots>
    </repository>
</repositories>
```

If you use a Maven mirror in `settings.xml`, make sure it does not block access to the Spring repositories:

```xml
<mirror>
    <id>my-mirror</id>
    <mirrorOf>*,!spring-snapshots,!central-portal-snapshots</mirrorOf>
    <url>https://my-mirror.example.com/maven</url>
</mirror>
```

## Dependency Management

The Spring AI Bill of Materials (BOM) centralizes the dependency versions for a release.

Import the BOM into your project so that Spring AI dependencies stay aligned:

```xml
<dependencyManagement>
    <dependencies>
        <dependency>
            <groupId>org.springframework.ai</groupId>
            <artifactId>spring-ai-bom</artifactId>
            <version>1.0.0</version>
            <type>pom</type>
            <scope>import</scope>
        </dependency>
    </dependencies>
</dependencyManagement>
```

If you are using Spring Boot, you can also rely on the Spring Boot dependency management stack where appropriate.

## Adding Dependencies

After the BOM is in place, add only the Spring AI modules you need for your use case.

Typical examples include:

- chat models,
- embeddings,
- vector stores,
- tool calling,
- retrieval augmented generation,
- audio and multimodality features.

Refer to the relevant topic pages in the documentation for the exact dependency coordinates.

## Spring AI Samples

Use the Spring AI samples and documentation examples as a reference when wiring your first application.

If you are exploring the project, start from the feature area you care about most and build outward from there.
