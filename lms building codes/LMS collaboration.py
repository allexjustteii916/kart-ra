#!/usr/bin/env python3
"""
collab_learning.py

A lightweight collaborative-learning prototype inspired by peer-driven LMS workflows.

Features:
- Employee skill profiles
- Skill-gap detection
- Mentor matching based on strengths vs. deficits
- Learning relationship creation
- Feedback/discussion threads
- Simple CLI demo

Run:
    python collab_learning.py
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import uuid


@dataclass
class Employee:
    employee_id: str
    name: str
    department: str
    skills: Dict[str, int] = field(default_factory=dict)
    learning_goals: Dict[str, int] = field(default_factory=dict)

    def skill_level(self, skill: str) -> int:
        return self.skills.get(skill, 0)


@dataclass
class FeedbackMessage:
    author_id: str
    message: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))


@dataclass
class LearningRelationship:
    relationship_id: str
    learner_id: str
    mentor_id: str
    skill: str
    target_level: int
    status: str = "active"
    messages: List[FeedbackMessage] = field(default_factory=list)


class CollaborativeLearningPlatform:
    def __init__(self) -> None:
        self.employees: Dict[str, Employee] = {}
        self.relationships: Dict[str, LearningRelationship] = {}

    def add_employee(
        self,
        name: str,
        department: str,
        skills: Optional[Dict[str, int]] = None,
        learning_goals: Optional[Dict[str, int]] = None,
    ) -> Employee:
        employee_id = str(uuid.uuid4())[:8]
        employee = Employee(
            employee_id=employee_id,
            name=name,
            department=department,
            skills=skills or {},
            learning_goals=learning_goals or {},
        )
        self.employees[employee_id] = employee
        return employee

    def find_skill_gaps(self, employee_id: str) -> List[Tuple[str, int, int]]:
        employee = self._get_employee(employee_id)
        gaps = []
        for skill, target_level in employee.learning_goals.items():
            current_level = employee.skill_level(skill)
            if current_level < target_level:
                gaps.append((skill, current_level, target_level))
        return sorted(gaps, key=lambda item: item[2] - item[1], reverse=True)

    def recommend_mentors(
        self,
        learner_id: str,
        skill: str,
        min_mentor_level: int = 3,
        limit: int = 5,
    ) -> List[Tuple[Employee, float]]:
        learner = self._get_employee(learner_id)
        learner_level = learner.skill_level(skill)

        ranked: List[Tuple[Employee, float]] = []

        for candidate in self.employees.values():
            if candidate.employee_id == learner_id:
                continue

            mentor_level = candidate.skill_level(skill)
            if mentor_level < min_mentor_level or mentor_level <= learner_level:
                continue

            skill_advantage = mentor_level - learner_level

            # Reward cross-functional learning slightly while still prioritizing skill strength.
            cross_department_bonus = 0.5 if candidate.department != learner.department else 0.0

            # Prefer mentors whose expertise comfortably exceeds the learner's current level.
            score = (mentor_level * 2.0) + skill_advantage + cross_department_bonus
            ranked.append((candidate, score))

        ranked.sort(key=lambda item: item[1], reverse=True)
        return ranked[:limit]

    def auto_match_for_all_gaps(
        self, learner_id: str
    ) -> List[Tuple[str, Optional[Employee], float]]:
        matches = []
        for skill, _, _ in self.find_skill_gaps(learner_id):
            mentors = self.recommend_mentors(learner_id, skill)
            if mentors:
                mentor, score = mentors[0]
                matches.append((skill, mentor, score))
            else:
                matches.append((skill, None, 0.0))
        return matches

    def create_learning_relationship(
        self,
        learner_id: str,
        mentor_id: str,
        skill: str,
        target_level: int,
    ) -> LearningRelationship:
        learner = self._get_employee(learner_id)
        mentor = self._get_employee(mentor_id)

        if learner_id == mentor_id:
            raise ValueError("Learner and mentor must be different employees.")

        if mentor.skill_level(skill) <= learner.skill_level(skill):
            raise ValueError(
                f"{mentor.name} is not currently stronger than {learner.name} in {skill}."
            )

        relationship_id = str(uuid.uuid4())[:8]
        relationship = LearningRelationship(
            relationship_id=relationship_id,
            learner_id=learner_id,
            mentor_id=mentor_id,
            skill=skill,
            target_level=target_level,
        )
        self.relationships[relationship_id] = relationship
        return relationship

    def post_feedback(
        self,
        relationship_id: str,
        author_id: str,
        message: str,
    ) -> FeedbackMessage:
        relationship = self._get_relationship(relationship_id)

        if author_id not in {relationship.learner_id, relationship.mentor_id}:
            raise ValueError("Only the learner or mentor can post in this thread.")

        feedback = FeedbackMessage(author_id=author_id, message=message)
        relationship.messages.append(feedback)
        return feedback

    def update_skill(self, employee_id: str, skill: str, new_level: int) -> None:
        employee = self._get_employee(employee_id)
        if not 0 <= new_level <= 5:
            raise ValueError("Skill levels must be between 0 and 5.")
        employee.skills[skill] = new_level

    def complete_relationship(self, relationship_id: str) -> None:
        relationship = self._get_relationship(relationship_id)
        relationship.status = "completed"

    def relationship_summary(self, relationship_id: str) -> str:
        relationship = self._get_relationship(relationship_id)
        learner = self._get_employee(relationship.learner_id)
        mentor = self._get_employee(relationship.mentor_id)

        lines = [
            f"Learning relationship: {relationship.relationship_id}",
            f"Learner: {learner.name}",
            f"Mentor: {mentor.name}",
            f"Skill: {relationship.skill}",
            f"Target level: {relationship.target_level}",
            f"Status: {relationship.status}",
            "Discussion:",
        ]

        if not relationship.messages:
            lines.append("  No messages yet.")
        else:
            for item in relationship.messages:
                author = self._get_employee(item.author_id)
                lines.append(f"  [{item.created_at}] {author.name}: {item.message}")

        return "\n".join(lines)

    def _get_employee(self, employee_id: str) -> Employee:
        try:
            return self.employees[employee_id]
        except KeyError as exc:
            raise KeyError(f"Unknown employee ID: {employee_id}") from exc

    def _get_relationship(self, relationship_id: str) -> LearningRelationship:
        try:
            return self.relationships[relationship_id]
        except KeyError as exc:
            raise KeyError(f"Unknown relationship ID: {relationship_id}") from exc


def demo() -> None:
    platform = CollaborativeLearningPlatform()

    maya = platform.add_employee(
        "Maya",
        "Marketing",
        skills={"copywriting": 4, "analytics": 1, "leadership": 2},
        learning_goals={"analytics": 4, "leadership": 3},
    )

    leo = platform.add_employee(
        "Leo",
        "Data",
        skills={"analytics": 5, "python": 4, "leadership": 3},
    )

    nina = platform.add_employee(
        "Nina",
        "Operations",
        skills={"leadership": 5, "analytics": 3, "project management": 5},
    )

    print("\nSKILL GAPS")
    for skill, current, target in platform.find_skill_gaps(maya.employee_id):
        print(f"- {skill}: current {current}, target {target}")

    print("\nMENTOR RECOMMENDATIONS")
    for skill, mentor, score in platform.auto_match_for_all_gaps(maya.employee_id):
        if mentor:
            print(f"- {skill}: {mentor.name} ({mentor.department}), score={score:.1f}")
        else:
            print(f"- {skill}: no suitable mentor found")

    relationship = platform.create_learning_relationship(
        learner_id=maya.employee_id,
        mentor_id=leo.employee_id,
        skill="analytics",
        target_level=4,
    )

    platform.post_feedback(
        relationship.relationship_id,
        leo.employee_id,
        "Start by reviewing your last campaign dashboard and identify three metrics that changed week over week.",
    )

    platform.post_feedback(
        relationship.relationship_id,
        maya.employee_id,
        "I found conversion rate, CAC, and email CTR changed the most. I'll document why.",
    )

    print("\nRELATIONSHIP")
    print(platform.relationship_summary(relationship.relationship_id))


if __name__ == "__main__":
    demo()
