# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, tools
from xml.sax.saxutils import escape
import re
import logging

try:
    # optional import; jika tidak tersedia, kita tangani saat fungsi dipanggil
    from google import genai
    from google.genai.errors import APIError
except Exception:
    genai = None
    APIError = Exception

_logger = logging.getLogger(__name__)


class WhapiMessage(models.Model):
    _name = 'whapi.message'
    _description = 'WHAPI Message'

    name = fields.Char("Message ID")
    # nomor dokumen/ticket otomatis (sequence) — disimpan terpisah di name_no
    name_no = fields.Char(string="Message No.", copy=False, readonly=True,
                          help="Auto-generated document/ticket number.")
    sender = fields.Char("From Number")
    recipient = fields.Char("To")
    chat_id = fields.Char("Chat ID")
    from_name = fields.Char("From Name")
    chat_name = fields.Char("Chat Name")
    text = fields.Text("Text")
    formatted_text = fields.Html("WA Text", compute="_compute_formatted_text", readonly=True, store=False)
    quoted_id = fields.Char("Quoted Message ID")
    quoted_author = fields.Char("Quoted Author")
    quoted_text = fields.Text("Quoted Text")
    # Perbaikan: gunakan Selection agar statusbar widget tidak crash
    status = fields.Selection(
        selection=[
            ('new', 'New'),
            ('unread', 'Unread'),
            ('read', 'Read'),
            ('archived', 'Archived'),
        ],
        string='Status',
        default='new',
        help="Status of the message (used by UI statusbar)."
    )
    from_me = fields.Boolean("From Me", default=False)
    payload = fields.Text("Raw Payload")
    received_at = fields.Datetime("Received At", default=fields.Datetime.now)
    message_type = fields.Char("Type")
    channel_id = fields.Char("Channel ID")
    chat_type = fields.Selection(
        selection=[
            ('single', 'Single Chat'),
            ('group', 'Group Chat'),
            ('unknown', 'Unknown')
        ],
        string='Chat Type',
        compute='_compute_message_attributes',
        store=True,
        readonly=False,
        default='single',
        help="Detected chat type: single (1:1) or group."
    )

    # NOTE: change to regular stored fields (not compute). We'll fill them in create/write.
    wa_category = fields.Char(
        string='WA Category',
        size=64,
        store=True,
        readonly=False,
        help="Primary category extracted from first #tag in message (uppercased)."
    )

    wa_tags = fields.Char(
        string='WA Tags',
        size=256,
        store=True,
        readonly=False,
        help="All tags extracted from message (uppercased), delimited by '; '."
    )

    gemini_summary_result = fields.Html(
        string="Hasil Ringkasan AI",
        readonly=False,
        help="Ringkasan yang dihasilkan oleh AI."
    )

    # helper boolean for views if you want to show/hide without using attrs
    has_gemini_summary = fields.Boolean(string="Has Gemini Summary", compute='_compute_has_gemini_summary', store=False)

    # project_id = fields.Many2one(
        # comodel_name='project.project',
        # string='Project',
        # ondelete='set null',
        # help='Project tujuan ketika membuat project.task dari pesan',
        # default=lambda self: self._get_default_project()
    # )

    def _display_name(self):
        return self.name or ((self.sender or '') + ': ' + (self.text or '')[:40])

    @api.depends('text')
    def _compute_formatted_text(self):
        """
        Convert simple inline markers and newlines to HTML:
        *bold* -> <b>bold</b>
        _italic_ -> <i>italic</i>
        \n -> <br/>
        Escape HTML first to avoid injection.
        """
        bold_re = re.compile(r'\*(.*?)\*', re.DOTALL)
        italic_re = re.compile(r'_(.*?)_', re.DOTALL)

        for rec in self:
            raw = rec.text or ''
            safe = escape(raw)
            try:
                # convert bold then italic
                safe = bold_re.sub(r'<b>\1</b>', safe)
                safe = italic_re.sub(r'<i>\1</i>', safe)
                # convert newlines to <br/>
                safe = safe.replace('\n', '<br/>')
            except Exception:
                safe = escape(raw)
            rec.formatted_text = safe

    @api.depends('gemini_summary_result')
    def _compute_has_gemini_summary(self):
        for rec in self:
            rec.has_gemini_summary = bool(rec.gemini_summary_result)

    @api.model
    def _normalize_phone(self, val):
        if not val:
            return None
        s = str(val).strip()
        s = s.split('@')[0]
        s = s.replace('whatsapp:', '')
        m = re.search(r'(\+?\d{6,20})', s)
        if not m:
            return None
        phone = m.group(1)
        if not phone.startswith('+'):
            phone = '+' + phone
        return phone

    @api.model
    def _determine_chat_type(self, chat_id, sender):
        """
        Logic:
        - if chat_id contains '@g.' or endswith '@g.us' -> group
        - if chat_id contains '@s.whatsapp.net' or endswith '@s.whatsapp.net' or chat_id looks like a number -> single
        - fallback: if sender looks like phone number -> single
        - else unknown
        """
        try:
            if not chat_id:
                # fallback to sender
                if sender and re.search(r'\d{6,}', str(sender)):
                    return 'single'
                return 'unknown'
            cid = str(chat_id).lower()
            if '@g.' in cid or cid.endswith('@g.us'):
                return 'group'
            if '@s.whatsapp.net' in cid or cid.endswith('@s.whatsapp.net'):
                return 'single'
            if re.match(r'^\+?\d+$', cid.replace('-', '')):
                return 'single'
        except Exception:
            pass
        return 'unknown'

    @api.model
    def _extract_tags(self, text):
        """
        Return (category, tags_string)
        - find tokens like #TOKEN (multiple consecutive # handled)
        - normalize tokens to uppercase, strip surrounding non-word
        - remove duplicates while preserving order
        """
        if not text:
            return None, None
        # ensure string
        s = str(text)
        # find #tokens (anything between # and whitespace or another #)
        raw_tokens = re.findall(r'#([^\s#]+)', s)
        if not raw_tokens:
            return None, None
        cleaned = []
        seen = set()
        for tok in raw_tokens:
            tok_clean = re.sub(r'^[^\w]+|[^\w]+$', '', tok, flags=re.UNICODE)
            if not tok_clean:
                continue
            tok_up = tok_clean.upper()
            if tok_up not in seen:
                seen.add(tok_up)
                cleaned.append(tok_up)
        if not cleaned:
            return None, None
        category = cleaned[0]
        tags_string = '; '.join(cleaned)
        return category, tags_string

    # keep this method name (used by some parts) but make it a simple attribute updater
    def _compute_message_attributes(self):
        """
        Backwards-compatible helper: compute chat_type and optionally set wa_category/wa_tags
        (This method no longer used as @api.depends for wa fields; create/write handle wa extraction.)
        """
        for rec in self:
            try:
                rec.chat_type = self._determine_chat_type(rec.chat_id, rec.sender)
            except Exception:
                rec.chat_type = 'unknown'
            # do NOT overwrite existing wa_category here; extraction is handled in create/write when appropriate

    def action_summarize_with_gemini(self):
        """ Send message text to Gemini API for summarization. """
        self.ensure_one()

        if genai is None:
            raise exceptions.UserError(_(
                "Gemini SDK tidak tersedia di System Anda. Instal paket google-genai jika ingin gunakan fitur ini."
            ))

        api_key = self.env['ir.config_parameter'].sudo().get_param('omu.ai.api.key')
        if not api_key:
            raise exceptions.UserError(_(
                "Gemini API Key tidak ditemukan. Harap atur di Pengaturan > Teknis > Parameter Sistem "
                "dengan kunci 'omu.ai.api.key'."
            ))

        # Use raw text (prefer text, fallback to formatted_text)
        description_text = (self.text or '') or (self.formatted_text or '')
        if not description_text:
            raise exceptions.UserError(_(
                "Tidak ada teks yang dapat diringkas pada pesan ini."
            ))

        system_prompt = (
            "Tugas Anda adalah menyusun teks yang diberikan "
            "dalam Bahasa Indonesia. "
            "Gunakan format Markdown untuk penekanan kata kunci."
        )

        ai_prompt_prefix = self.env['ir.config_parameter'].sudo().get_param('omu.ai.prompt') or ''
        user_prompt = ai_prompt_prefix + description_text

        try:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[user_prompt],
                config=genai.types.GenerateContentConfig(
                    system_instruction=system_prompt,
                )
            )
            # response.text is the convenient property
            if getattr(response, 'text', None):
                self.gemini_summary_result = response.text
            else:
                self.gemini_summary_result = _("Gemini tidak dapat menghasilkan ringkasan. Respon API kosong.")
                _logger.error("Gemini API returned an empty/unknown response: %s", response)
        except APIError as e:
            error_msg = _("Kesalahan API Gemini: %s. Periksa API Key dan kuota Anda." % str(e))
            self.gemini_summary_result = error_msg
            _logger.error("Gemini API Error: %s", str(e))
            raise exceptions.UserError(error_msg)
        except Exception as e:
            error_msg = _("Terjadi kesalahan tak terduga saat memanggil Gemini: %s" % str(e))
            self.gemini_summary_result = error_msg
            _logger.error("Unexpected Error: %s", str(e))
            raise exceptions.UserError(error_msg)

    # @api.model
    # def _get_default_project(self):
        # """Return the project.record named 'Default'. If not exists, create it."""
        # env = self.env
        # try:
            # proj = env['project.project'].sudo().search([('name', '=', 'Default')], limit=1)
            # if proj:
                # return proj.id
            # # create the default project if not found (if model exists)
            # if 'project.project' in env:
                # proj = env['project.project'].sudo().create({'name': 'Default'})
                # return proj.id
        # except Exception as e:
            # _logger.warning("Could not get/create default project 'Default': %s", e)
        # return False

    @api.model
    def create(self, vals):
        """
        Robust create: accept both dict (single) and list (bulk).
        For each record: assign name_no sequence (if missing), try extract wa_category/wa_tags,
        then create and post-process (task creation, ensure wa fields).
        """
        def _create_single(local_vals):
            # local_vals must be a dict
            if not isinstance(local_vals, dict):
                _logger.warning("whapi.message.create: expected dict for single create, got %r", type(local_vals))
                local_vals = {}

            # Assign sequence to name_no if not provided
            if not local_vals.get('name_no'):
                try:
                    seq_code = 'whapi.message'
                    seq = self.env['ir.sequence'].sudo().next_by_code(seq_code)
                    if seq:
                        local_vals['name_no'] = seq
                except Exception as e:
                    _logger.warning("whapi.message: failed to assign sequence '%s': %s", seq_code, e)

            # Attempt to extract tags from incoming values (prefer explicit vals)
            try:
                incoming_text = local_vals.get('text') or local_vals.get('formatted_text') or local_vals.get('quoted_text') or ''
                if incoming_text and not local_vals.get('wa_category'):
                    cat, tags = self._extract_tags(incoming_text)
                    if cat:
                        local_vals['wa_category'] = cat
                    if tags:
                        local_vals['wa_tags'] = tags
            except Exception:
                _logger.exception("whapi.message: tag extraction failed during create input processing")

            # create the record (use super)
            rec = super(WhapiMessage, self).create(local_vals)

            # Post-create: ensure wa fields are present if still empty (extract from real record)
            try:
                if not rec.wa_category or not rec.wa_tags:
                    cat, tags = self._extract_tags(rec.text or rec.quoted_text or '')
                    updates = {}
                    if cat and not rec.wa_category:
                        updates['wa_category'] = cat
                    if tags and not rec.wa_tags:
                        updates['wa_tags'] = tags
                    if updates:
                        rec.sudo().write(updates)
            except Exception:
                _logger.exception("whapi.message: tag extraction failed after create")

            # prepare & create project.task if present
            try:
                task_vals = {
                    'name': (rec.sender or rec.name or 'Message from WHAPI')[:256],
                    'description': rec.formatted_text or rec.text or '',
                }
                try:
                    if rec.project_id:
                        task_vals['project_id'] = rec.project_id.id
                except Exception:
                    pass

                if 'project.task' in self.env:
                    self.env['project.task'].sudo().create(task_vals)
            except Exception as e:
                _logger.warning('Could not create project.task for whapi.message %s: %s', getattr(rec, 'id', '?'), e)
                
            # --- immediately sync tag_ids from wa_tags (ensure tags created and linked) ---
            try:
                # use sudo to avoid ACL issues
                rec.sudo()._sync_tags_from_wa_tags()
            except Exception:
                _logger.exception("Failed automatic tag sync after create for whapi.message %s", getattr(rec, 'id', '?'))
                

            return rec

        # --- Entry point: detect list vs dict ---
        if isinstance(vals, list):
            created_recs = []
            for item in vals:
                try:
                    rec = _create_single(item if isinstance(item, dict) else {})
                    created_recs.append(rec)
                except Exception:
                    _logger.exception("whapi.message.create: failed to create item in bulk create: %r", item)
            # return combined recordset
            return self.browse([r.id for r in created_recs])
        else:
            # single path: ensure we have a dict (defensive)
            if not isinstance(vals, dict):
                _logger.warning("whapi.message.create: expected dict or list, got %r; coercing to dict()", type(vals))
                try:
                    vals = dict(vals)
                except Exception:
                    vals = {}
            return _create_single(vals)

    def write(self, vals):
        """
        On write, if text or quoted_text is updated, re-extract wa_category/wa_tags unless explicit values provided.
        """
        # If caller explicitly sets wa_category/wa_tags, respect it.
        should_extract = False
        if ('text' in vals or 'quoted_text' in vals) and not (vals.get('wa_category') or vals.get('wa_tags')):
            should_extract = True

        # If we can extract from incoming values, do it before write so they are part of the write.
        if should_extract:
            text_for_tags = vals.get('text') or vals.get('quoted_text') or ''
            try:
                cat, tags = self._extract_tags(text_for_tags)
                if cat and not vals.get('wa_category'):
                    vals['wa_category'] = cat
                if tags and not vals.get('wa_tags'):
                    vals['wa_tags'] = tags
            except Exception:
                _logger.exception("whapi.message: tag extraction failed during write input processing")

        result = super(WhapiMessage, self).write(vals)

        # Post-write: ensure that any records that still lack wa_category/wa_tags get filled from current fields
        try:
            for rec in self:
                if not rec.wa_category or not rec.wa_tags:
                    cat, tags = self._extract_tags(rec.text or rec.quoted_text or '')
                    updates = {}
                    if cat and not rec.wa_category:
                        updates['wa_category'] = cat
                    if tags and not rec.wa_tags:
                        updates['wa_tags'] = tags
                    if updates:
                        rec.sudo().write(updates)
        except Exception:
            _logger.exception("whapi.message: tag extraction failed after write")

        return result

        # after post-write tag extraction
        try:
            self.sudo()._sync_tags_from_wa_tags()
        except Exception:
            _logger.exception("Failed automatic tag sync after write for whapi.message %s", ','.join(map(str, self.ids)))


    def action_mark_read(self):
        """Mark the message as read - set status to 'read'."""
        # ensure we use selection value
        self.ensure_one()
        try:
            self.write({'status': 'read'})
        except Exception as e:
            _logger.error('Failed to mark read for %s: %s', self.id, e)
            raise
        return True

    def action_archive(self):
        """Archive the message - set status to 'archived'."""
        self.ensure_one()
        try:
            self.write({'status': 'archived'})
        except Exception as e:
            _logger.error('Failed to archive %s: %s', self.id, e)
            raise
        return True
        
# --- Di dalam class WhapiMessage: tambahkan field many2many ---
    tag_ids = fields.Many2many(
        comodel_name='whapi.tag',
        relation='whapi_message_tag_rel',
        column1='message_id',
        column2='tag_id',
        string='Tags',
        help='Tags derived from WA Tags (automatically created/linked).'
    )

# --- Helper untuk memastikan tag records ada; return recordset ---
    @api.model
    def _ensure_tags(self, tag_names):
        """
        Given iterable of tag names (strings), ensure whapi.tag records exist (create if needed).
        Returns recordset of whapi.tag (using sudo to avoid ACL issues).
        """
        if not tag_names:
            return self.env['whapi.tag']
        # normalize names: strip + uppercase (or preserve case if you prefer)
        clean = []
        seen = set()
        for t in tag_names:
            if not t:
                continue
            tn = str(t).strip().upper()
            if not tn:
                continue
            if tn not in seen:
                seen.add(tn)
                clean.append(tn)
        if not clean:
            return self.env['whapi.tag']

        Tag = self.env['whapi.tag'].sudo()
        existing = Tag.search([('name', 'in', clean)])
        existing_names = {r.name for r in existing}
        to_create = [n for n in clean if n not in existing_names]
        created = []
        for name in to_create:
            try:
                created.append(Tag.create({'name': name}))
            except Exception:
                _logger.exception("Failed to create whapi.tag %s", name)
        # return union
        return (existing | self.env['whapi.tag'].sudo().browse([c.id for c in created]))

# --- Helper sinkronisasi per-record; parse wa_tags string and write tag_ids ---
    def _sync_tags_from_wa_tags(self):
        """
        For each record in self, parse rec.wa_tags (semicolon-separated) into tag names,
        ensure tag records exist and link them to rec.tag_ids.
        """
        for rec in self:
            try:
                raw = rec.wa_tags or ''
                # wa_tags expected like 'TAG1; TAG2; TAG3'
                names = [p.strip() for p in raw.split(';') if p and p.strip()]
                # uppercase normalization to match _ensure_tags
                names = [n.upper() for n in names]
                if names:
                    tags = self._ensure_tags(names)
                    # Use sudo() when writing tags to avoid ACL problems in webhook context
                    rec.sudo().write({'tag_ids': [(6, 0, tags.ids)]})
                else:
                    # if no names found, clear tag_ids (optional; comment out if you prefer keep)
                    rec.sudo().write({'tag_ids': [(5, 0, 0)]})  # (5) clear all links
            except Exception:
                _logger.exception("Failed to sync tags for whapi.message %s", rec.id)


# --- Model Tag sederhana ---
class WhapiTag(models.Model):
    _name = 'whapi.tag'
    _description = 'WHAPI Tag'

    name = fields.Char(string='Nama Tag', required=True, index=True)
    color = fields.Integer(string='Warna')  # optional, untuk UI warna tag

    _sql_constraints = [
        ('whapi_tag_name_uniq', 'UNIQUE(name)', 'Tag name must be unique.')
    ]

