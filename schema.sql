CREATE TABLE IF NOT EXISTS `apps` (
    `id` TEXT NOT NULL,
    `name` TEXT NOT NULL,
    `website` TEXT,
    `redirect_uris` TEXT NOT NULL,
    `client_id` TEXT NOT NULL,
    `client_secret` TEXT NOT NULL,
    `vapid_key` TEXT NOT NULL,
    `scopes` TEXT NOT NULL,
    `last_used_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`)
);
