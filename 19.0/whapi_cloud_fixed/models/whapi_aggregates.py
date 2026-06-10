# -*- coding: utf-8 -*-
from odoo import models, fields

class WhapiDailyCounts(models.Model):
    _name = 'whapi.daily.counts'
    _description = 'Daily Message Count'
    _auto = False

    id = fields.Id()
    day = fields.Date('Tanggal')
    message_count = fields.Integer('Total Pesan')

    def init(self):
        """Materialized View: total pesan per hari"""
        self.env.cr.execute("""
            DROP MATERIALIZED VIEW IF EXISTS whapi_daily_counts CASCADE;
            CREATE MATERIALIZED VIEW whapi_daily_counts AS
            SELECT
                row_number() OVER ()::bigint AS id,
                (date_trunc('day', received_at AT TIME ZONE 'UTC'))::date AS day,
                COUNT(*) AS message_count
            FROM whapi_message
            GROUP BY day
            ORDER BY day;
        """)


class WhapiChannelCounts(models.Model):
    _name = 'whapi.channel.counts'
    _description = 'Message Count per Channel'
    _auto = False

    id = fields.Id()
    channel_name = fields.Char('Channel')
    message_count = fields.Integer('Jumlah Pesan')

    def init(self):
        """Materialized View: total pesan per channel/chat
        Use m.channel_id::text to avoid dependency on a separate whapi_channel table.
        """
        self.env.cr.execute("""
            DROP MATERIALIZED VIEW IF EXISTS whapi_channel_counts CASCADE;
            CREATE MATERIALIZED VIEW whapi_channel_counts AS
            SELECT
                row_number() OVER ()::bigint AS id,
                COALESCE(m.channel_id::text, 'Unknown') AS channel_name,
                COUNT(m.id) AS message_count
            FROM whapi_message m
            GROUP BY channel_name
            ORDER BY message_count DESC;
        """)
        

class WhapiCategoryCounts(models.Model):
    _name = 'whapi.category.counts'
    _description = 'Message Count per WA Category'
    _auto = False

    id = fields.Id()
    wa_category = fields.Char('WA Category')
    message_count = fields.Integer('Jumlah Pesan')

    def init(self):
        """Materialized View: total pesan per kategori WA"""
        self.env.cr.execute("""
            DROP MATERIALIZED VIEW IF EXISTS whapi_category_counts CASCADE;
            CREATE MATERIALIZED VIEW whapi_category_counts AS
            SELECT
                row_number() OVER ()::bigint AS id,
                wa_category AS wa_category,
                COUNT(*) AS message_count
            FROM whapi_message
            WHERE wa_category IS NOT NULL
            GROUP BY wa_category
            ORDER BY message_count DESC;
        """)


class WhapiTagCounts(models.Model):
    _name = 'whapi.tag.counts'
    _description = 'Message Count per Tag'
    _auto = False

    id = fields.Id()
    tag_name = fields.Char('Tag')
    message_count = fields.Integer('Jumlah Pesan')

    def init(self):
        """
        Create materialized view whapi_tag_counts that counts messages per tag.
        Uses the many2many relation table 'whapi_message_tag_rel' with columns:
            - message_id
            - tag_id
        """
        self.env.cr.execute("""
            DROP MATERIALIZED VIEW IF EXISTS whapi_tag_counts CASCADE;
            CREATE MATERIALIZED VIEW whapi_tag_counts AS
            SELECT
                row_number() OVER ()::bigint AS id,
                t.name AS tag_name,
                COUNT(m.id) AS message_count
            FROM whapi_tag t
            JOIN whapi_message_tag_rel mt ON mt.tag_id = t.id
            JOIN whapi_message m ON m.id = mt.message_id
            GROUP BY t.name
            ORDER BY message_count DESC;
        """)