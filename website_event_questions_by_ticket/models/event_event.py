# Copyright 2019 Tecnativa - Pedro M. Baeza
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class EventEvent(models.Model):
    _inherit = "event.event"

    def _question_tickets(self, question):
        """Tickets of this event a question is limited to. A reusable question
        can be shared by several events: tickets of the other events do not
        restrict it here (empty = all tickets)."""
        return question.restricted_ticket_ids.filtered(lambda t: t.event_id == self)

    def _get_specific_questions(self, ticket_id):
        self.ensure_one()
        return self.specific_question_ids.filtered(
            lambda x: (
                not self._question_tickets(x)
                or ticket_id in self._question_tickets(x).ids
            )
        )

    def _get_general_questions(self, ticket_ids):
        self.ensure_one()
        return self.general_question_ids.filtered(
            lambda x: (
                not self._question_tickets(x)
                or (set(ticket_ids) & set(self._question_tickets(x).ids))
            )
        )


class EventQuestion(models.Model):
    _inherit = "event.question"

    restricted_ticket_ids = fields.Many2many(
        comodel_name="event.event.ticket",
        string="Limited to tickets",
        domain="[('event_id', 'in', event_ids)]",
        ondelete="restrict",
    )
