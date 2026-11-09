-- 오늘 뭐 입지? — MySQL 8.0 스키마 (참고용)
-- 실제 테이블 생성은 backend 폴더에서 'alembic upgrade head' 로 하세요. 이 파일은 alembic 결과를 덤프한 것입니다.


CREATE TABLE `users` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `email` varchar(255) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `nickname` varchar(30) NOT NULL,
  `default_location_name` varchar(100) DEFAULT NULL COMMENT '예: 서울 마포구',
  `default_latitude` decimal(9,6) DEFAULT NULL,
  `default_longitude` decimal(9,6) DEFAULT NULL,
  `preferred_styles` json DEFAULT NULL COMMENT '선호 스타일 ["미니멀", ...]',
  `created_at` datetime NOT NULL DEFAULT (now()),
  `updated_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_users_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='회원';
CREATE TABLE `clothing_items` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint NOT NULL,
  `name` varchar(100) NOT NULL COMMENT '예: 옥스퍼드 셔츠',
  `category` varchar(20) NOT NULL,
  `sub_category` varchar(50) DEFAULT NULL COMMENT '예: 라운드넥 니트',
  `color_name` varchar(30) DEFAULT NULL COMMENT '예: 네이비',
  `color_hex` varchar(7) DEFAULT NULL COMMENT '#2C3A57',
  `seasons` json NOT NULL COMMENT '["FALL","WINTER"]',
  `styles` json NOT NULL COMMENT '["미니멀","캐주얼"]',
  `material` varchar(50) DEFAULT NULL COMMENT '예: 울 혼방',
  `warmth_level` smallint NOT NULL DEFAULT '3' COMMENT '보온성 1(얇음)~5(매우 두꺼움)',
  `is_waterproof` tinyint(1) NOT NULL DEFAULT '0',
  `image_url` varchar(500) NOT NULL COMMENT '배경 제거된 이미지',
  `original_image_url` varchar(500) DEFAULT NULL COMMENT '원본 업로드 이미지',
  `ai_analysis` json DEFAULT NULL,
  `is_verified` tinyint(1) NOT NULL DEFAULT '0' COMMENT '사용자 검수 완료 여부',
  `status` varchar(20) NOT NULL DEFAULT 'ACTIVE',
  `wear_count` int NOT NULL DEFAULT '0',
  `last_worn_at` date DEFAULT NULL,
  `memo` varchar(500) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  `updated_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `ix_clothing_items_user_category` (`user_id`,`category`),
  KEY `ix_clothing_items_user_status` (`user_id`,`status`),
  CONSTRAINT `fk_clothing_items_user_id_users` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `ck_clothing_items_category` CHECK ((`category` in (_utf8mb4'TOP',_utf8mb4'BOTTOM',_utf8mb4'OUTER',_utf8mb4'DRESS',_utf8mb4'SHOES',_utf8mb4'BAG',_utf8mb4'ACCESSORY'))),
  CONSTRAINT `ck_clothing_items_clothingstatus` CHECK ((`status` in (_utf8mb4'ACTIVE',_utf8mb4'LAUNDRY',_utf8mb4'ARCHIVED'))),
  CONSTRAINT `ck_clothing_items_warmth_level_range` CHECK ((`warmth_level` between 1 and 5))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='옷장 아이템';
CREATE TABLE `schedules` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint NOT NULL,
  `date` date NOT NULL,
  `title` varchar(100) NOT NULL,
  `start_time` time DEFAULT NULL,
  `end_time` time DEFAULT NULL,
  `location` varchar(100) DEFAULT NULL,
  `is_outdoor` tinyint(1) DEFAULT NULL COMMENT '실외 일정 여부 (모르면 NULL)',
  `is_important` tinyint(1) NOT NULL DEFAULT '0' COMMENT '주요 일정 (코디 기준이 됨)',
  `source` varchar(20) NOT NULL DEFAULT 'MANUAL',
  `external_id` varchar(255) DEFAULT NULL COMMENT '외부 캘린더 이벤트 ID',
  `created_at` datetime NOT NULL DEFAULT (now()),
  `updated_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_schedules_external` (`user_id`,`source`,`external_id`),
  KEY `ix_schedules_user_date` (`user_id`,`date`),
  CONSTRAINT `fk_schedules_user_id_users` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `ck_schedules_schedulesource` CHECK ((`source` in (_utf8mb4'MANUAL',_utf8mb4'GOOGLE')))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='일정';
CREATE TABLE `recommendations` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint NOT NULL,
  `target_date` date NOT NULL,
  `location_name` varchar(100) DEFAULT NULL,
  `latitude` decimal(9,6) DEFAULT NULL,
  `longitude` decimal(9,6) DEFAULT NULL,
  `weather` json NOT NULL,
  `schedule_snapshot` json DEFAULT NULL,
  `situations` json NOT NULL COMMENT '["발표","저녁 약속"]',
  `mood` varchar(20) DEFAULT NULL,
  `user_note` varchar(500) DEFAULT NULL COMMENT 'AI에게 더 알려줄 것',
  `status` varchar(20) NOT NULL DEFAULT 'PENDING',
  `llm_model` varchar(50) DEFAULT NULL,
  `error_message` varchar(500) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `ix_recommendations_user_date` (`user_id`,`target_date`),
  CONSTRAINT `fk_recommendations_user_id_users` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `ck_recommendations_mood` CHECK ((`mood` in (_utf8mb4'COMFY',_utf8mb4'NEAT',_utf8mb4'DRESSY'))),
  CONSTRAINT `ck_recommendations_recommendationstatus` CHECK ((`status` in (_utf8mb4'PENDING',_utf8mb4'COMPLETED',_utf8mb4'FAILED')))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='코디 추천 요청';
CREATE TABLE `outfits` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `recommendation_id` bigint NOT NULL,
  `rank` smallint NOT NULL COMMENT '1부터 시작하는 추천 순위',
  `summary` varchar(300) DEFAULT NULL COMMENT '한 줄 추천 이유 (홈 카드)',
  `reasons` json DEFAULT NULL,
  `tips` json DEFAULT NULL COMMENT '["셔츠 소매를 한 번 접어...", ...]',
  `is_selected` tinyint(1) NOT NULL DEFAULT '0' COMMENT '''이걸로 입을게요'' 선택 여부',
  `selected_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_outfits_rec_rank` (`recommendation_id`,`rank`),
  CONSTRAINT `fk_outfits_recommendation_id_recommendations` FOREIGN KEY (`recommendation_id`) REFERENCES `recommendations` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='추천 코디 조합';
CREATE TABLE `outfit_items` (
  `outfit_id` bigint NOT NULL,
  `clothing_item_id` bigint NOT NULL,
  `slot` varchar(20) NOT NULL COMMENT '코디 내 역할',
  PRIMARY KEY (`outfit_id`,`clothing_item_id`),
  KEY `fk_outfit_items_clothing_item_id_clothing_items` (`clothing_item_id`),
  CONSTRAINT `fk_outfit_items_clothing_item_id_clothing_items` FOREIGN KEY (`clothing_item_id`) REFERENCES `clothing_items` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_outfit_items_outfit_id_outfits` FOREIGN KEY (`outfit_id`) REFERENCES `outfits` (`id`) ON DELETE CASCADE,
  CONSTRAINT `ck_outfit_items_category` CHECK ((`slot` in (_utf8mb4'TOP',_utf8mb4'BOTTOM',_utf8mb4'OUTER',_utf8mb4'DRESS',_utf8mb4'SHOES',_utf8mb4'BAG',_utf8mb4'ACCESSORY')))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='코디 구성 아이템';
CREATE TABLE `outfit_feedbacks` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `outfit_id` bigint NOT NULL,
  `user_id` bigint NOT NULL,
  `rating` varchar(20) NOT NULL,
  `reasons` json DEFAULT NULL COMMENT '["TOO_COLD","TOO_FORMAL","IN_LAUNDRY"]',
  `comment` varchar(500) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  `updated_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_outfit_feedbacks_outfit_id` (`outfit_id`),
  KEY `fk_outfit_feedbacks_user_id_users` (`user_id`),
  CONSTRAINT `fk_outfit_feedbacks_outfit_id_outfits` FOREIGN KEY (`outfit_id`) REFERENCES `outfits` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_outfit_feedbacks_user_id_users` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `ck_outfit_feedbacks_feedbackrating` CHECK ((`rating` in (_utf8mb4'LIKE',_utf8mb4'DISLIKE')))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='코디 피드백';


