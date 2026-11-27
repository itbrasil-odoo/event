# Copyright 2017 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import Command, api, fields, models
from odoo.tools import frozendict

SYNC_KEYS = ("interval_nbr", "interval_unit", "interval_type", "template_ref")


class EventEvent(models.Model):
    _inherit = "event.event"

    event_mail_template_id = fields.Many2one(
        comodel_name="event.mail.template",
        string="Mail Template Scheduler",
        compute="_compute_event_mail_template_id",
        store=True,
        readonly=False,
        precompute=True,
    )

    @api.depends("company_id")
    def _compute_event_mail_template_id(self):
        """Default template of the event's company, not of the active one."""
        for event in self:
            if not event.event_mail_template_id:
                company = event.company_id or self.env.company
                event.event_mail_template_id = company.event_mail_template_id

    @api.depends("event_mail_template_id")
    def _compute_event_mail_ids(self):
        records = self.filtered("event_mail_template_id")
        without_template = self - records
        for event in records:
            # Same rule as the core sync: keep lines already sent or with
            # registrations (their history), add the template lines missing.
            mails_to_remove = event.event_mail_ids.filtered(
                lambda mail: (
                    not mail._origin.mail_done
                    and not mail._origin.mail_registration_ids
                )
            )
            command = [Command.unlink(mail.id) for mail in mails_to_remove]
            kept = {
                frozendict(mail._prepare_event_mail_values())
                for mail in event.event_mail_ids - mails_to_remove
            }
            for line in event.event_mail_template_id.scheduler_template_ids:
                values = line._prepare_event_mail_values()
                # Compare on the keys event.mail itself provides.
                same = frozendict({key: values[key] for key in SYNC_KEYS})
                if same not in kept:
                    command.append(Command.create(values))
            if command:
                event.event_mail_ids = command
        return super(EventEvent, without_template)._compute_event_mail_ids()
