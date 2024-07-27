CREATE TABLE IF NOT EXISTS `apps` (
    `id` TEXT PRIMARY KEY NOT NULL,
    `name` TEXT NOT NULL,
    `website` TEXT,
    `redirect_uris` TEXT NOT NULL,
    `client_id` TEXT NOT NULL,
    `client_secret` TEXT NOT NULL,
    `vapid_key` TEXT NOT NULL,
    `scopes` TEXT NOT NULL,
    `session_id` TEXT,
    `authorization_code` TEXT,
    `access_token` TEXT,
    `last_used_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (`session_id`) REFERENCES `sessions`(`session_id`)
);
CREATE TABLE IF NOT EXISTS `sessions` (
    `session_id` TEXT PRIMARY KEY NOT NULL,
    `cookies` TEXT NOT NULL,
    `username` TEXT NOT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
