package sensepro.controller.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;

@Slf4j
@Service
public class FileService<T> {

    private final ObjectMapper objectMapper = new ObjectMapper();

    public synchronized T readFile(String fileName, Class<T> valueType) throws FileServiceException {
        try {
            Path filePath = Path.of(fileName);
            String content = Files.readString(filePath);
            log.debug("File {} read successfully!", fileName);

            // Deserialize JSON content to the specified type
            return objectMapper.readValue(content, valueType);
        } catch (IOException e) {
            log.error("Failed to read file {}: {}", fileName, e.getMessage());
            throw new FileServiceException("Error reading file " + fileName, e);
        }
    }

    public synchronized void writeFile(String fileName, Object object) {
        try {
            Path filePath = Path.of(fileName);
            String jsonContent = objectMapper.writeValueAsString(object);
            Files.writeString(filePath, jsonContent, StandardOpenOption.CREATE, StandardOpenOption.TRUNCATE_EXISTING);
            log.debug("File {} written successfully!", fileName);
        } catch (IOException e) {
            log.error("Failed to write file {}: {}", fileName, e.getMessage());
            throw new FileServiceException("Error writing to file " + fileName, e);
        }
    }
}
