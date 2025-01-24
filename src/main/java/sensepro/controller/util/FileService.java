package sensepro.controller.util;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;

@Service
public class FileService<T> {

    private final Logger logger = LoggerFactory.getLogger(FileService.class);
    private final ObjectMapper objectMapper = new ObjectMapper();

    public T readFile(String fileName, Class<T> valueType) throws IOException {
        Path filePath = Path.of(fileName);
        String content = Files.readString(filePath);
        logger.debug("File {} read successfully!", fileName);
        return objectMapper.readValue(content, valueType);
    }

    public void writeFile(String fileName, T object) throws IOException {
        Path filePath = Path.of(fileName);
        String jsonContent = objectMapper.writeValueAsString(object);
        Files.writeString(filePath, jsonContent, StandardOpenOption.CREATE, StandardOpenOption.TRUNCATE_EXISTING);
        logger.debug("File {} written successfully!", fileName);
    }
}
