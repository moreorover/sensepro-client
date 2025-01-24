package sensepro.controller.util;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.junit.jupiter.api.io.TempDir;
import org.mockito.junit.jupiter.MockitoExtension;
import sensepro.controller.model.Config;
import sensepro.controller.service.FileService;

import java.io.IOException;
import java.nio.file.Path;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;

@ExtendWith(MockitoExtension.class)
public class FileServiceTests {
    @TempDir
    Path tempDir;

    @Test
    void testReadAndWriteFile() throws IOException {
        FileService<String> fileService = new FileService<>();
        String fileName = tempDir.resolve("test.json").toString();
        String content = "{\"name\":\"John\",\"age\":30}";

        // Write
        fileService.writeFile(fileName, content);

        // Read
        String readContent = fileService.readFile(fileName, String.class);

        assertEquals(content, readContent);
    }

    @Test
    void testWriteAndReadObject() throws IOException {
        FileService<Person> fileService = new FileService<>();
        String fileName = tempDir.resolve("person.json").toString();

        // Create a sample Person object
        Person person = new Person();
        person.setId("123");
        person.setName("John Doe");

        // Write the Person object to the file
        fileService.writeFile(fileName, person);

        // Read the Person object from the file
        Person readPerson = fileService.readFile(fileName, Person.class);

        // Assert that the written and read objects are equivalent
        assertEquals(person.getId(), readPerson.getId());
        assertEquals(person.getName(), readPerson.getName());
    }

    @Test
    void testReadConfigFile() throws IOException {
        FileService<Config> fileService = new FileService<>();

        // Resolve the path to the config.json file in the test resources folder
        String fileName = Path.of("src", "test", "resources", "config.json").toString();

        // Read the content of the config.json file
        Config config = fileService.readFile(fileName, Config.class);

        // Assertions to validate the content of config.json
        assertNotNull(config);
        assertEquals("cm5wmlkpu0004d3ns31v1zv9q", config.controllerId);
        assertEquals("cm5wmlkpu0004d3ns31v1zv9q", config.controller.id);
        assertEquals("cm5wmlkqa000ad3ns36org5zw", config.devices.get(0).id);
    }

    static class Person {
        private String id;
        private String name;

        public String getId() {
            return id;
        }

        public void setId(String id) {
            this.id = id;
        }

        public String getName() {
            return name;
        }

        public void setName(String name) {
            this.name = name;
        }
    }
}
