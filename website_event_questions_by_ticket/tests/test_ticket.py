# Copyright 2020 Studio73 - Ioan Galan
# Copyright 2023 Tecnativa - Carolina Fernandez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from dateutil.relativedelta import relativedelta

from odoo import Command, fields

from odoo.addons.base.tests.common import BaseCommon


class TestTicket(BaseCommon):
    _test_user_groups = ("base.group_user", "event.group_event_manager")

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        now = fields.Datetime.now()
        cls.event_1 = cls.env["event.event"].create(
            {
                "name": "Event One",
                "date_begin": now + relativedelta(days=1),
                "date_end": now + relativedelta(days=3),
                "organizer_id": cls.partner.id,
            }
        )
        cls.ticket_1 = cls.env["event.event.ticket"].create(
            {"name": "Ticket One", "event_id": cls.event_1.id}
        )
        cls.ticket_2 = cls.env["event.event.ticket"].create(
            {"name": "Ticket Two", "event_id": cls.event_1.id}
        )
        cls.question_1 = cls.env["event.question"].create(
            {
                "title": "Question Two",
                "event_ids": [Command.set(cls.event_1.ids)],
                "restricted_ticket_ids": [Command.set(cls.ticket_1.ids)],
            }
        )

    def test_specific_questions(self):
        specific_questions_1 = self.event_1._get_specific_questions(self.ticket_1.id)
        self.assertIn(self.question_1, specific_questions_1)
        specific_questions_2 = self.event_1._get_specific_questions(self.ticket_2.id)
        self.assertNotIn(self.question_1, specific_questions_2)

    def test_general_questions(self):
        general_questions_1 = self.event_1._get_general_questions(self.ticket_1.ids)
        self.assertNotIn(self.question_1, general_questions_1)
        general_questions_2 = self.event_1._get_general_questions(self.ticket_2.ids)
        self.assertNotIn(self.question_1, general_questions_2)

    def test_general_question_limited_to_ticket(self):
        question = self.env["event.question"].create(
            {
                "title": "General limited",
                "once_per_order": True,
                "event_ids": [Command.set(self.event_1.ids)],
                "restricted_ticket_ids": [Command.set(self.ticket_1.ids)],
            }
        )
        self.assertIn(question, self.event_1._get_general_questions(self.ticket_1.ids))
        self.assertNotIn(
            question, self.event_1._get_general_questions(self.ticket_2.ids)
        )

    def test_shared_question_not_hidden_in_other_event(self):
        now = fields.Datetime.now()
        event_2 = self.env["event.event"].create(
            {
                "name": "Event Two",
                "date_begin": now + relativedelta(days=1),
                "date_end": now + relativedelta(days=3),
            }
        )
        ticket_b = self.env["event.event.ticket"].create(
            {"name": "Ticket B", "event_id": event_2.id}
        )
        self.question_1.event_ids = [Command.link(event_2.id)]
        self.assertIn(self.question_1, event_2._get_specific_questions(ticket_b.id))
        self.assertNotIn(
            self.question_1, self.event_1._get_specific_questions(self.ticket_2.id)
        )
