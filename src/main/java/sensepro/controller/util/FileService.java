package sensepro.controller.util;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;

@Service
public class FileService {

    private final Logger logger = LoggerFactory.getLogger(FileService.class);

    public void writeFile(String fileName, String text) {
        Path filePath = Path.of(fileName);

        try {
            Files.writeString(filePath, text, StandardOpenOption.CREATE, StandardOpenOption.TRUNCATE_EXISTING);
            logger.debug("File {} written successfully!", fileName);
        } catch (IOException e) {
            logger.error(e.getMessage());
        }
    }
}
