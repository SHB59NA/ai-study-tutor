from dataclasses import dataclass, field


@dataclass
class LearnerProgress:
    scores: list[float] = field(default_factory=list)

    def add_score(self, score: float) -> None:
        self.scores.append(max(0.0, min(1.0, score)))
        # Keep the model intentionally simple and transparent for the MVP.
        self.scores = self.scores[-10:]

    @property
    def mastery_score(self) -> float:
        if not self.scores:
            return 0.5
        return sum(self.scores) / len(self.scores)

    @property
    def next_difficulty(self) -> str:
        mastery = self.mastery_score
        if mastery < 0.5:
            return "beginner"
        if mastery < 0.8:
            return "intermediate"
        return "advanced"
