package sensepro.controller.service;

import jakarta.annotation.PostConstruct;
import lombok.extern.slf4j.Slf4j;
import org.apache.hc.client5.http.auth.*;
import org.apache.hc.client5.http.classic.methods.HttpGet;
import org.apache.hc.client5.http.impl.classic.CloseableHttpClient;
import org.apache.hc.client5.http.impl.classic.CloseableHttpResponse;
import org.apache.hc.client5.http.impl.classic.HttpClients;
import org.apache.hc.client5.http.impl.auth.BasicCredentialsProvider;
import org.apache.hc.core5.http.io.entity.EntityUtils;
import org.apache.hc.core5.http.protocol.HttpCoreContext;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import sensepro.controller.model.Config;
import sensepro.controller.mq.MessagePublisher;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.URI;
import java.util.Objects;

@Slf4j
@Service
public class MotionDetectionListener {

    private final FileService<Config> fileService;
    private final MessagePublisher messagePublisher;

    public MotionDetectionListener(FileService<Config> fileService, MessagePublisher messagePublisher) {
        this.fileService = fileService;
        this.messagePublisher = messagePublisher;
    }

    @Value("${sensepro.cctv.password}")
    private String password;


    @PostConstruct
    public void startListening() {
        log.info("Initializing Motion Detection...");
        Config config;
        try {
            config = fileService.readFile("config.json", Config.class);
            log.info("Successfully read config.json");
        } catch (FileServiceException e) {
            log.error(e.getMessage());
            config = null;
        }

        if (config == null) {
            log.warn("No config.json found. Waiting for initial configuration from MQ Server...");
            messagePublisher.sendMessage("server-notifications", "No config.json found.");
            return;
        }

        if (config.devices.isEmpty()) {
            log.warn("No devices found. Waiting for initial configuration from MQ Server...");
            messagePublisher.sendMessage("server-notifications", "No devices found.");
            return;
        }

        config.devices.stream().filter(device -> Objects.equals(device.deviceTypeId, "cctv") && device.ip != null).forEach(device -> new Thread(() -> listenToEvents(device.ip)).start());
    }

    private void listenToEvents(String ip) {
        String username = "admin";
        String eventUrl = "http://" + ip + "/cgi-bin/eventManager.cgi?action=attach&codes=[VideoMotion]&heartbeat=5";
        while (true) {
            try {
                log.info("Connecting to: {}", eventUrl);

                // Set up Digest Authentication
                BasicCredentialsProvider credentialsProvider = new BasicCredentialsProvider();
                credentialsProvider.setCredentials(new AuthScope(ip, 80), new UsernamePasswordCredentials(username, password.toCharArray()));

                try (CloseableHttpClient httpClient = HttpClients.custom().setDefaultCredentialsProvider(credentialsProvider).build()) {

                    HttpCoreContext context = HttpCoreContext.create();

                    HttpGet request = new HttpGet(URI.create(eventUrl));
                    request.setHeader("Accept", "text/plain");

                    // Execute the request
                    try (CloseableHttpResponse response = httpClient.execute(request, context)) {
                        int statusCode = response.getCode();
                        if (statusCode == 200) {
                            log.info("✅ Successfully connected to the camera API!");
                            log.info("Waiting for motion detection events...");

                            try (BufferedReader reader = new BufferedReader(new InputStreamReader(response.getEntity().getContent()))) {
                                String line;
                                while ((line = reader.readLine()) != null) {
                                    if (!line.isEmpty()) {
                                        log.info("Motion Event: {}", line);
                                    }
                                }
                            }
                        } else {
                            log.error("❌ Failed to connect. HTTP Status Code: {}", statusCode);
                            log.error("Response: {}", EntityUtils.toString(response.getEntity()));
                        }
                    }
                }
            } catch (Exception e) {
                log.error("❌ Error connecting to the camera: {}", e.getMessage());
            }

            log.error("Retrying connection in 5 seconds...");
            try {
                Thread.sleep(5000);
            } catch (InterruptedException ignored) {
            }
        }
    }
}