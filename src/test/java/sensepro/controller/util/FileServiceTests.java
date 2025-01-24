package sensepro.controller.util;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.junit.jupiter.api.io.TempDir;
import org.mockito.junit.jupiter.MockitoExtension;

import java.io.IOException;
import java.nio.file.Path;

import static org.junit.jupiter.api.Assertions.assertEquals;

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

    static class Person {
        private String id;
        private String name;

        // Getters and setters
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
