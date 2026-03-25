
-- --- AUDIT LOG: 2026-03-25 01:34:07 ---
CREATE TABLE "account_dimension" (id SERIAL NOT NULL, "create_uid" int4, "write_uid" int4, "name" VARCHAR NOT NULL, "code" VARCHAR NOT NULL, "create_date" timestamp, "write_date" timestamp, PRIMARY KEY(id)); COMMENT ON TABLE "account_dimension" IS 'Chiều phân tích'; COMMENT ON COLUMN "account_dimension"."create_uid" IS 'Created by'; COMMENT ON COLUMN "account_dimension"."write_uid" IS 'Last Updated by'; COMMENT ON COLUMN "account_dimension"."name" IS 'Tên chiều PT'; COMMENT ON COLUMN "account_dimension"."code" IS 'Mã chiều PT'; COMMENT ON COLUMN "account_dimension"."create_date" IS 'Created on'; COMMENT ON COLUMN "account_dimension"."write_date" IS 'Last Updated on';
ALTER TABLE "account_dimension" ADD CONSTRAINT "account_dimension_check_code_uniq" unique(code);
COMMENT ON CONSTRAINT "account_dimension_check_code_uniq" ON "account_dimension" IS 'unique(code)';
ALTER TABLE "account_dimension" ADD FOREIGN KEY ("create_uid") REFERENCES "res_users"("id") ON DELETE set null;
ALTER TABLE "account_dimension" ADD FOREIGN KEY ("write_uid") REFERENCES "res_users"("id") ON DELETE set null;

-- --- AUDIT LOG: 2026-03-25 01:54:51 ---
CREATE TABLE "business_segment" (id SERIAL NOT NULL, "create_uid" int4, "write_uid" int4, "name" VARCHAR NOT NULL, "code" VARCHAR NOT NULL, "create_date" timestamp, "write_date" timestamp, PRIMARY KEY(id)); COMMENT ON TABLE "business_segment" IS 'Mảng kinh doanh'; COMMENT ON COLUMN "business_segment"."create_uid" IS 'Created by'; COMMENT ON COLUMN "business_segment"."write_uid" IS 'Last Updated by'; COMMENT ON COLUMN "business_segment"."name" IS 'Tên mảng KD'; COMMENT ON COLUMN "business_segment"."code" IS 'Mã mảng KD'; COMMENT ON COLUMN "business_segment"."create_date" IS 'Created on'; COMMENT ON COLUMN "business_segment"."write_date" IS 'Last Updated on';
ALTER TABLE "business_segment" ADD CONSTRAINT "business_segment_check_code_uniq" unique(code);
COMMENT ON CONSTRAINT "business_segment_check_code_uniq" ON "business_segment" IS 'unique(code)';
ALTER TABLE "business_segment" ADD FOREIGN KEY ("create_uid") REFERENCES "res_users"("id") ON DELETE set null;
ALTER TABLE "business_segment" ADD FOREIGN KEY ("write_uid") REFERENCES "res_users"("id") ON DELETE set null;

-- --- AUDIT LOG: 2026-03-25 02:33:36 ---
CREATE TABLE "dimension_account_rel" ("dimension_id" INTEGER NOT NULL,
                                          "account_id" INTEGER NOT NULL,
                                          PRIMARY KEY("dimension_id", "account_id"));
                    COMMENT ON TABLE "dimension_account_rel" IS 'RELATION BETWEEN account_dimension AND account_account';
                    CREATE INDEX ON "dimension_account_rel" ("account_id", "dimension_id");
ALTER TABLE "account_dimension" ADD COLUMN "company_id" int4 ; COMMENT ON COLUMN "account_dimension"."company_id" IS 'Công ty áp dụng';
ALTER TABLE "account_dimension" ALTER COLUMN "code" DROP NOT NULL;
CREATE TABLE "account_dimension_value" (id SERIAL NOT NULL, "dimension_id" int4, "create_uid" int4, "write_uid" int4, "code" VARCHAR, "name" VARCHAR NOT NULL, "create_date" timestamp, "write_date" timestamp, PRIMARY KEY(id)); COMMENT ON TABLE "account_dimension_value" IS 'account.dimension.value'; COMMENT ON COLUMN "account_dimension_value"."dimension_id" IS 'Thuộc chiều phân tích'; COMMENT ON COLUMN "account_dimension_value"."create_uid" IS 'Created by'; COMMENT ON COLUMN "account_dimension_value"."write_uid" IS 'Last Updated by'; COMMENT ON COLUMN "account_dimension_value"."code" IS 'Mã'; COMMENT ON COLUMN "account_dimension_value"."name" IS 'Tên giá trị'; COMMENT ON COLUMN "account_dimension_value"."create_date" IS 'Created on'; COMMENT ON COLUMN "account_dimension_value"."write_date" IS 'Last Updated on';
ALTER TABLE "account_dimension" ALTER COLUMN "company_id" SET NOT NULL;
ALTER TABLE "dimension_account_rel" ADD FOREIGN KEY ("dimension_id") REFERENCES "account_dimension"("id") ON DELETE cascade;
ALTER TABLE "dimension_account_rel" ADD FOREIGN KEY ("account_id") REFERENCES "account_account"("id") ON DELETE cascade;
ALTER TABLE "account_dimension" ADD FOREIGN KEY ("company_id") REFERENCES "res_company"("id") ON DELETE restrict;
ALTER TABLE "account_dimension_value" ADD FOREIGN KEY ("dimension_id") REFERENCES "account_dimension"("id") ON DELETE cascade;
ALTER TABLE "account_dimension_value" ADD FOREIGN KEY ("create_uid") REFERENCES "res_users"("id") ON DELETE set null;
ALTER TABLE "account_dimension_value" ADD FOREIGN KEY ("write_uid") REFERENCES "res_users"("id") ON DELETE set null;

-- --- AUDIT LOG: 2026-03-25 02:34:20 ---
CREATE TABLE "dimension_account_rel" ("dimension_id" INTEGER NOT NULL,
                                          "account_id" INTEGER NOT NULL,
                                          PRIMARY KEY("dimension_id", "account_id"));
                    COMMENT ON TABLE "dimension_account_rel" IS 'RELATION BETWEEN account_dimension AND account_account';
                    CREATE INDEX ON "dimension_account_rel" ("account_id", "dimension_id");
ALTER TABLE "account_dimension" ADD COLUMN "company_id" int4 ; COMMENT ON COLUMN "account_dimension"."company_id" IS 'Công ty áp dụng';
ALTER TABLE "account_dimension" ALTER COLUMN "code" DROP NOT NULL;
CREATE TABLE "account_dimension_value" (id SERIAL NOT NULL, "dimension_id" int4, "create_uid" int4, "write_uid" int4, "code" VARCHAR, "name" VARCHAR NOT NULL, "create_date" timestamp, "write_date" timestamp, PRIMARY KEY(id)); COMMENT ON TABLE "account_dimension_value" IS 'account.dimension.value'; COMMENT ON COLUMN "account_dimension_value"."dimension_id" IS 'Thuộc chiều phân tích'; COMMENT ON COLUMN "account_dimension_value"."create_uid" IS 'Created by'; COMMENT ON COLUMN "account_dimension_value"."write_uid" IS 'Last Updated by'; COMMENT ON COLUMN "account_dimension_value"."code" IS 'Mã'; COMMENT ON COLUMN "account_dimension_value"."name" IS 'Tên giá trị'; COMMENT ON COLUMN "account_dimension_value"."create_date" IS 'Created on'; COMMENT ON COLUMN "account_dimension_value"."write_date" IS 'Last Updated on';
ALTER TABLE "account_dimension" ALTER COLUMN "company_id" SET NOT NULL;
ALTER TABLE "dimension_account_rel" ADD FOREIGN KEY ("dimension_id") REFERENCES "account_dimension"("id") ON DELETE cascade;
ALTER TABLE "dimension_account_rel" ADD FOREIGN KEY ("account_id") REFERENCES "account_account"("id") ON DELETE cascade;
ALTER TABLE "account_dimension" ADD FOREIGN KEY ("company_id") REFERENCES "res_company"("id") ON DELETE restrict;
ALTER TABLE "account_dimension_value" ADD FOREIGN KEY ("dimension_id") REFERENCES "account_dimension"("id") ON DELETE cascade;
ALTER TABLE "account_dimension_value" ADD FOREIGN KEY ("create_uid") REFERENCES "res_users"("id") ON DELETE set null;
ALTER TABLE "account_dimension_value" ADD FOREIGN KEY ("write_uid") REFERENCES "res_users"("id") ON DELETE set null;

-- --- AUDIT LOG: 2026-03-25 02:39:44 ---
CREATE TABLE "dimension_account_rel" ("dimension_id" INTEGER NOT NULL,
                                          "account_id" INTEGER NOT NULL,
                                          PRIMARY KEY("dimension_id", "account_id"));
                    COMMENT ON TABLE "dimension_account_rel" IS 'RELATION BETWEEN account_dimension AND account_account';
                    CREATE INDEX ON "dimension_account_rel" ("account_id", "dimension_id");
ALTER TABLE "account_dimension" ADD COLUMN "company_id" int4 ; COMMENT ON COLUMN "account_dimension"."company_id" IS 'Công ty áp dụng';
ALTER TABLE "account_dimension" ALTER COLUMN "code" DROP NOT NULL;
CREATE TABLE "account_dimension_value" (id SERIAL NOT NULL, "dimension_id" int4, "create_uid" int4, "write_uid" int4, "code" VARCHAR, "name" VARCHAR NOT NULL, "create_date" timestamp, "write_date" timestamp, PRIMARY KEY(id)); COMMENT ON TABLE "account_dimension_value" IS 'account.dimension.value'; COMMENT ON COLUMN "account_dimension_value"."dimension_id" IS 'Thuộc chiều phân tích'; COMMENT ON COLUMN "account_dimension_value"."create_uid" IS 'Created by'; COMMENT ON COLUMN "account_dimension_value"."write_uid" IS 'Last Updated by'; COMMENT ON COLUMN "account_dimension_value"."code" IS 'Mã'; COMMENT ON COLUMN "account_dimension_value"."name" IS 'Tên giá trị'; COMMENT ON COLUMN "account_dimension_value"."create_date" IS 'Created on'; COMMENT ON COLUMN "account_dimension_value"."write_date" IS 'Last Updated on';
ALTER TABLE "account_dimension" ALTER COLUMN "company_id" SET NOT NULL;
ALTER TABLE "dimension_account_rel" ADD FOREIGN KEY ("dimension_id") REFERENCES "account_dimension"("id") ON DELETE cascade;
ALTER TABLE "dimension_account_rel" ADD FOREIGN KEY ("account_id") REFERENCES "account_account"("id") ON DELETE cascade;
ALTER TABLE "account_dimension" ADD FOREIGN KEY ("company_id") REFERENCES "res_company"("id") ON DELETE restrict;
ALTER TABLE "account_dimension_value" ADD FOREIGN KEY ("dimension_id") REFERENCES "account_dimension"("id") ON DELETE cascade;
ALTER TABLE "account_dimension_value" ADD FOREIGN KEY ("create_uid") REFERENCES "res_users"("id") ON DELETE set null;
ALTER TABLE "account_dimension_value" ADD FOREIGN KEY ("write_uid") REFERENCES "res_users"("id") ON DELETE set null;
