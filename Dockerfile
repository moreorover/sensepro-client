# Stage 1: Build the application
FROM maven:3.9.4-eclipse-temurin-17 AS build

# Set working directory
WORKDIR /app

# Copy Maven project files to the container
COPY pom.xml .
COPY src ./src

# Build the Spring Boot application
RUN mvn clean package -DskipTests

# Stage 2: Run the application
FROM eclipse-temurin:17

# Set working directory
WORKDIR /app

# Copy the JAR file from the build stage
COPY --from=build /app/target/controller-*.jar app.jar

# Expose the application's port
EXPOSE 8080

# Set the entry point to run the Spring Boot application
ENTRYPOINT ["java", "-jar", "app.jar"]
