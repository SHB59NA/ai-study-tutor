from dataclasses import dataclass, field


@dataclass
class LearnerProgress:
    scores: list[float] = field(default_factory=list)
    concept_scores: dict[str, list[float]] = field(default_factory=dict)

    def add_score(self, score: float, concept: str | None = None) -> None:
        bounded = max(0.0, min(1.0, score))
        self.scores.append(bounded)
        self.scores = self.scores[-10:]

        if concept:
            key = concept.strip()
            history = self.concept_scores.setdefault(key, [])
            history.append(bounded)
            self.concept_scores[key] = history[-5:]

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

    @property
    def weak_concepts(self) -> list[dict]:
        items: list[dict] = []
        for concept, scores in self.concept_scores.items():
            if not scores:
                continue
            mastery = sum(scores) / len(scores)
            if mastery < 0.75:
                items.append(
                    {
                        "concept": concept,
                        "attempts": len(scores),
                        "mastery": round(mastery, 3),
                    }
                )
        items.sort(key=lambda item: (item["mastery"], -item["attempts"]))
        return items[:5]

    @property
    def weakest_concept(self) -> str | None:
        weak = self.weak_concepts
        return weak[0]["concept"] if weak else None
