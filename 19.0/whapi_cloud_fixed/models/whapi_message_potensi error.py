# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _
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

    wa_category = fields.Char(
        string='WA Category',
        size=64,
        compute='_compute_message_attributes',
        store=True,
        readonly=False,
        help="Primary category extracted from first #tag in message (uppercased)."
    )

    wa_tags = fields.Char(
        string='WA Tags',
        size=256,
        compute='_compute_message_attributes',
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

    project_id = fields.Many2one(
        comodel_name='project.project',
        string='Project',
        ondelete='set null',
        help='Project tujuan ketika membuat project.task dari pesan',
        default=lambda self: self._get_default_project()
    )

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
        raw_tokens = re.findall(r'#([^\s#]+)', text)
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

    @api.depends('chat_id', 'sender', 'text', 'quoted_text')
    def _compute_message_attributes(self):
        for rec in self:
            # compute chat_type
            try:
                rec.chat_type = self._determine_chat_type(rec.chat_id, rec.sender)
            except Exception:
                rec.chat_type = 'unknown'

            # extract tags
            category = None
            tags = None
            try:
                category, tags = self._extract_tags(rec.text or '')
                if not category and rec.quoted_text:
                    category, tags = self._extract_tags(rec.quoted_text or '')
            except Exception:
                category, tags = None, None

            rec.wa_category = category
            rec.wa_tags = tags

    def action_summarize_with_gemini(self):
        """ Send message text to Gemini API for summarization. """
        self.ensure_one()

        if genai is None:
            raise exceptions.UserError(_(
                "Gemini SDK tidak tersedia di environment. Instal paket google-genai jika ingin gunakan fitur ini."
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

    @api.model
    def _get_default_project(self):
        """Return the project.record named 'Default'. If not exists, create it."""
        env = self.env
        try:
            proj = env['project.project'].sudo().search([('name', '=', 'Default')], limit=1)
            if proj:
                return proj.id
            # create the default project if not found (if model exists)
            if 'project.project' in env:
                proj = env['project.project'].sudo().create({'name': 'Default'})
                return proj.id
        except Exception as e:
            _logger.warning("Could not get/create default project 'Default': %s", e)
        return False

    @api.model
    def create(self, vals):
        """
        Create whapi.message record.
        If no name_no provided, attempt to assign sequence 'whapi.message' to vals['name_no'].
        Existing behavior (create task etc.) is preserved.
        """
        # Assign sequence to name_no if not provided
        if not vals.get('name_no'):
            try:
                seq_code = 'whapi.message'
                seq = self.env['ir.sequence'].sudo().next_by_code(seq_code)
                if seq:
                    vals['name_no'] = seq
            except Exception as e:
                _logger.warning("whapi.message: failed to assign sequence '%s': %s", seq_code, e)

        # create the whapi.message record (preserve existing behavior)
        rec = super(WhapiMessage, self).create(vals)

        # prepare task values (preserve existing behavior)
        task_vals = {
            'name': (rec.sender or rec.name or 'Message from WHAPI')[:256],
            'description': rec.formatted_text or rec.text or '',
        }

        # If message has project_id set, assign it to task
        try:
            if rec.project_id:
                task_vals['project_id'] = rec.project_id.id
        except Exception:
            pass

        # try to create a project.task; if project module missing, log and continue
        try:
            if 'project.task' in self.env:
                # using sudo to avoid access rights issue on automation
                self.env['project.task'].sudo().create(task_vals)
        except Exception as e:
            _logger.warning('Could not create project.task for whapi.message %s: %s', rec.id, e)

        return rec


    def action_create_task(self):
        """Manual action to create a task from this message record."""
        self.ensure_one()
        task_vals = {
            'name': (self.sender or self.name or 'Message from WHAPI')[:256],
            'description': self.formatted_text or self.text or '',
        }
        if self.project_id:
            task_vals['project_id'] = self.project_id.id
        try:
            if 'project.task' in self.env:
                # create task with sudo to avoid access rights issues
                task = self.env['project.task'].sudo().create(task_vals)
                return task
            else:
                _logger.warning("project.task model not available - cannot create task")
                return False
        except Exception as e:
            _logger.error('Failed to create task from message %s: %s', self.id, e)
            return False

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
